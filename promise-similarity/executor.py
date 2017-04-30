import argparse
import json
import requests
import os
import csv

from slugify import slugify
from tagger import Tagger
from similarity_calculator import SimilarityCalculator


class Executor():

    def __init__(self):
        self.data_dir          = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data')
        self.promise_file      = os.path.join(self.data_dir, 'promises.csv')
        self.lemma_file        = os.path.join(self.data_dir, 'lemmas.json')
        self.similarities_file = os.path.join(self.data_dir, 'similarities.json')
        self.result_file       = os.path.join(self.data_dir, 'result.json')
        self.stop_words_file   = os.path.join(self.data_dir, 'ton_idf.txt')

        parser = argparse.ArgumentParser(
            description='Calculate promise similarity.')

        parser.add_argument("-o", "--obt-path", type=str,
                            help="Path to Oslo-Bergen-Tagger.")

        parser.add_argument('-n', '--no-cache',
                            default=[],
                            type=str,
                            nargs='*',
                            help="Things that shouldn't be cached.")

        self.args = parser.parse_args()

    def execute(self):
        self.setup()
        self.tag()
        self.calculate_promise_similarities()
        self.consolidate()
        self.calculate_program_similarities()

    def setup(self):
        if (not os.path.exists(self.promise_file)) or 'download' in self.args.no_cache:
            print('Downloading promises')
            self.download(
                'https://files.holderdeord.no/data/2017/internal/promises.csv', self.promise_file)

        if (not os.path.exists(self.stop_words_file)) or 'stop_words' in self.args.no_cache:
            print('Downloading stop words')
            self.download(
                'https://files.holderdeord.no/data/2017/internal/ton_idf.txt', self.stop_words_file)

        self.read_promises()

    def download(self, url, path):
        r = requests.get(url, stream=True)

        with open(path, 'w') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

    def tag(self):
        if (not os.path.exists(self.lemma_file)) or 'tag' in self.args.no_cache:
            print('Tagging')
            self.lemmas = Tagger(self.args.obt_path, self.promises).tag()

            with open(self.lemma_file, 'w') as out:
                out.write(json.dumps(self.lemmas))
        else:
            print('Reading lemmas')
            with open(self.lemma_file, 'r') as file:
                self.lemmas = json.load(file)

    def calculate_promise_similarities(self):
        if (not os.path.exists(self.similarities_file)) or 'similarities' in self.args.no_cache:
            print('Calculating similarity')
            docs = [' '.join(sentence) for sentence in self.lemmas]
            self.similarities = SimilarityCalculator(docs).get()

            with open(self.similarities_file, 'w') as out:
                out.write(json.dumps(self.similarities))
        else:
            print('Reading similarities')
            with open(self.similarities_file, 'r') as file:
                self.similarities = json.load(file)

    def consolidate(self):
        print('Writing result')

        result = []

        for sim in self.similarities:
            related_promises = []

            for related in sim['related']:
                if related['index'] != sim['index']:
                    related_promises.append({
                        "id": int(self.promises[related['index']]['id']),
                        "score": related['score']
                    })

            result.append({
                "id": int(self.promises[sim['index']]['id']),
                "related": related_promises
            })

        with open(self.result_file, 'w') as out:
            out.write(json.dumps(result))

    def calculate_program_similarities(self):
        print('Calculating program similarities')
        programs = {}

        for promise in self.promises:
            slug = slugify(promise['promisor'] + '-' +
                           promise['period'])

            if slug not in programs:
                programs[slug] = []

            programs[slug].append(promise)

        slugs = programs.keys()
        texts = []

        for promises in programs.values():
            full_text = []

            for promise in promises:
                full_text.append(promise['body'])

            texts.append('\n'.join(full_text))

        stop_words = []
        with open(os.path.join(self.data_dir, 'ton_idf.txt'), 'r') as f:
            for line in f:
                stop_words.append(line.split(' ')[0])

        similarities = SimilarityCalculator(
            texts, top=20, stop_words=stop_words).get()
        result = []

        for sim in similarities:
            result.append({
                'slug': slugs[sim['index']],
                'related': [{
                    'score': related['score'],
                    'slug': slugs[related['index']]
                } for related in sim['related']]
            })

        with open(os.path.join(self.data_dir, 'program-similarities.json'), 'w') as out:
            out.write(json.dumps(result))

    def read_promises(self):
        print('Reading promises')
        self.promises = []

        with open(self.promise_file, 'r') as csvfile:
            for row in csv.DictReader(csvfile):
                self.promises.append(row)
