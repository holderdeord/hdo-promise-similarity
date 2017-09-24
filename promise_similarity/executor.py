# coding=utf-8

import argparse
import json

import requests
import os
import csv

from slugify import slugify
from .tagger import Tagger
from .similarity_calculator import SimilarityCalculator


class Executor:
    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
        self.default_tagger_path = os.path.join(self.base_dir, 'obt')

        self.data_dir          = os.path.join(self.base_dir, 'data')
        self.promise_file      = os.path.join(self.data_dir, 'promises.csv')
        self.lemma_file        = os.path.join(self.data_dir, 'lemmas.json')
        self.similarities_file = os.path.join(self.data_dir, 'similarities.json')
        self.result_file       = os.path.join(self.data_dir, 'result.json')
        self.stop_words_file   = os.path.join(self.data_dir, 'ton_idf.txt')

        self.duplicates_result_file = os.path.join(self.data_dir, 'duplicates.tsv')

        self.program_similarities_file = os.path.join(self.data_dir, 'program-similarities.json')
        self.program_reuse_file        = os.path.join(self.data_dir, 'program-reuse.json')

    def parse_args(self):
        parser = argparse.ArgumentParser(
            description='Calculate promise similarity.')
        parser.add_argument("-o", "--obt-path", type=str, default=self.default_tagger_path,
                            help="Path to Oslo-Bergen-Tagger.")

        parser.add_argument('-n', '--no-cache',
                            default=[],
                            type=str,
                            nargs='*',
                            help="Things that shouldn't be cached.")

        self.args = parser.parse_args()

    def execute(self):
        self.parse_args()
        self.download_deps()
        self.tag()
        self.calculate_promise_similarities()
        self.write_duplicate_spreadsheet()
        self.consolidate()
        self.calculate_program_similarities()
        self.calculate_program_reuse()

    def download_deps(self):
        if (not os.path.exists(self.promise_file)) or 'download' in self.args.no_cache:
            print('Downloading promises')
            self.download(
                'https://files.holderdeord.no/data/csv/promises.csv', self.promise_file)

        if (not os.path.exists(self.stop_words_file)) or 'stop_words' in self.args.no_cache:
            print('Downloading stop words')
            self.download(
                'https://files.holderdeord.no/data/2017/internal/ton_idf.txt', self.stop_words_file)

        self.read_promises()

    def download(self, url, path):
        r = requests.get(url, stream=True)

        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    def tag(self):
        if (not os.path.exists(self.lemma_file)) or 'tag' in self.args.no_cache:
            print('Tagging')
            self.lemmas = Tagger(self.args.obt_path, self.promises).tag()

            self.save_json(self.lemma_file, self.lemmas)
        else:
            print('Reading lemmas')
            with open(self.lemma_file, 'r') as file:
                self.lemmas = json.load(file)

    def calculate_promise_similarities(self):
        if (not os.path.exists(self.similarities_file)) or 'similarities' in self.args.no_cache:
            print('Calculating similarity')
            docs = [' '.join(sentence) for sentence in self.lemmas]
            self.similarities = SimilarityCalculator(docs, threshold=0.7).get()

            self.save_json(self.similarities_file, self.similarities)
        else:
            print('Reading similarities')
            with open(self.similarities_file, 'r') as file:
                self.similarities = json.load(file)

    def write_duplicate_spreadsheet(self):
        """ Find possible duplicate promises which are not self, have same promisor in same period """
        print('Writing spreadsheet')

        result = []
        pairs = []
        columns = ['original', 'promisor', 'period', 'score', 'id', 'body', 'url']
        url_template = 'https://lofter.holderdeord.no/?q={}&ids=true'
        count = 0

        for sim in self.similarities:
            org_inserted = False
            for related in sim['related']:
                org = self.promises[sim['index']]
                rel = self.promises[related['index']]
                pair = {org['id'], rel['id']}
                same_promise = related['index'] == sim['index']
                same_promisor = org['promisor'] == rel['promisor']
                same_period = org['period'] == rel['period']
                if not same_promise and same_promisor and same_period and related['score'] >= 0.8 and pair not in pairs:
                    pairs.append(pair)  # only add a pair once

                    if not org_inserted:
                        org_data = {
                            "original": 'Y',
                            "promisor": org['promisor'],
                            "period": org['period'],
                            "id": org['id'],
                            "body": org['body'],
                            'score': '',
                            'url': url_template.format(org['id'])
                        }
                        result.append(org_data)
                        org_inserted = True

                    hit = {
                        "original": '',
                        "promisor": org['promisor'],
                        "period": org['period'],
                        "id": rel['id'],
                        "body": rel['body'],
                        "score": related['score'],
                        'url': url_template.format(rel['id'])
                    }
                    result.append(hit)
                    count += 1

        self.save_tsv(self.duplicates_result_file, columns, result)

        print('Wrote {} possible dupliates to {}'.format(count, self.duplicates_result_file))

    def consolidate(self):
        print('Writing result')

        result = []

        for sim in self.similarities:
            related_promises = []

            for related in sim['related']:
                related_promises.append({
                    "id": self.promises[related['index']]['id'],
                    "score": related['score']
                })

            if len(sim['related']):
                result.append({
                    "id": self.promises[sim['index']]['id'],
                    "related": related_promises
                })

        self.save_json(self.result_file, result)

    def calculate_program_similarities(self):
        print('Calculating program similarities')
        programs = {}

        for promise in self.promises:
            slug = slugify(promise['promisor'] + '-' + promise['period'])

            if slug not in programs:
                programs[slug] = []

            programs[slug].append(promise)

        slugs = list(programs.keys())
        texts = []

        for promises in programs.values():
            full_text = []

            for promise in promises:
                full_text.append(promise['body'])

            texts.append(' '.join(full_text))

        stop_words = []
        with open(os.path.join(self.data_dir, 'ton_idf.txt'), 'r') as f:
            for line in f:
                stop_words.append(line.split(' ')[0])

        similarities = SimilarityCalculator(texts, top=20, stop_words=stop_words).get()
        result = []

        for sim in similarities:
            result.append({
                'slug': slugs[sim['index']],
                'related': [{
                    'score': related['score'],
                    'slug': slugs[related['index']]
                } for related in sim['related']]
            })

        self.save_json(self.program_similarities_file, result)

    """
    1. Hvor mange løfter i partiets program har over >90% likehet med løfter i foregående periodes program?
    2. Hvor mange løfter i regjeringsplattformen har over >90% likhet løfter i med respektive partienes program?
    """
    def calculate_program_reuse(self):
        if (not os.path.exists(self.program_reuse_file)) or 'program_reuse' in self.args.no_cache:
            print('Calculating program reuse')

            threshold = 0.7
            by_promisor = {}
            reuse = {}
            sim_by_index = {}

            for sim in self.similarities:
                sim_by_index[sim['index']] = {}

                for r in sim['related']:
                    if r['score'] >= threshold:
                        sim_by_index[sim['index']][r['index']] = 1

            for promise in self.promises:
                promisor = promise['promisor']
                period = promise['period']

                if promisor not in by_promisor:
                    by_promisor[promisor] = {}

                if period not in by_promisor[promisor]:
                    by_promisor[promisor][period] = []

                by_promisor[promisor][period].append(promise)

            for promisor, periods in by_promisor.items():
                for period, promises in periods.items():
                    slug = ':'.join([promisor, period])

                    if slug not in reuse:
                        reuse[slug] = {}

                    for compared_promisor, compared_periods in by_promisor.items():
                        for compared_period, compared_promises in compared_periods.items():
                            compared_slug = ':'.join([compared_promisor, compared_period])

                            if compared_slug not in reuse[slug]:
                                reuse[slug][compared_slug] = { 'count': 0 }

                            print('Comparing {} with {}'.format(slug, compared_slug))

                            for promise in promises:
                                for compared_promise in compared_promises:
                                    if promise['index'] in sim_by_index:
                                        related = sim_by_index[promise['index']]

                                        if compared_promise['index'] in related:
                                            reuse[slug][compared_slug]['count'] += 1

                            for stat in reuse[slug].values():
                                stat['percentage'] = stat['count'] * 100 / len(promises)

            self.program_reuse = reuse
            self.save_json(self.program_reuse_file, reuse)
        else:
            print('Reading program reuse')
            with open(self.program_reuse_file, 'r') as file:
                self.program_reuse = json.load(file)

        keys = list(self.program_reuse.keys())
        columns = [''] + keys;
        rows = []

        for slug, comparisons in self.program_reuse.items():
            row = {'': slug}

            for key in keys:
                if key in comparisons:
                    row[key] = comparisons[key]['percentage']
                else:
                    row[key] = '-'

            rows.append(row)

        self.save_tsv(self.program_reuse_file.replace('.json', '.tsv'), columns, rows)

    def read_promises(self):
        print('Reading promises')
        self.promises = []

        with open(self.promise_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for (index, row) in enumerate(reader):
                row['index'] = index
                row['id'] = int(row['id'])

                self.promises.append(row)

    def save_json(self, file_name, data):
        with open(file_name, 'w') as out:
            json.dump(data, out, ensure_ascii=False)

    def save_tsv(self, file_name, columns, data):
        with open(file_name, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, columns, delimiter="\t")
            writer.writeheader()
            writer.writerows(data)
