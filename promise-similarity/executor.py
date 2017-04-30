import argparse
import json
import requests
import os
import csv

from tagger import Tagger
from similarity_calculator import SimilarityCalculator


class Executor():

    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), '../data')

        self.promise_file = os.path.join(self.data_dir, 'promises.csv')
        self.lemma_file = os.path.join(self.data_dir, 'lemmas.json')
        self.similarities_file = os.path.join(
            self.data_dir, 'similarities.json')
        self.result_file = os.path.join(self.data_dir, 'result.json')

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
        self.download()
        self.tag()
        self.calculate_similarities()
        self.consolidate()

    def download(self):
        if (not os.path.exists(self.promise_file)) or 'download' in self.args.no_cache:
            print('Downloading')

            r = requests.get(
                'https://files.holderdeord.no/data/2017/internal/promises.csv', stream=True)

            with open(self.promise_file, 'w') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

        self.read_promises()

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

    def calculate_similarities(self):
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

    def read_promises(self):
        print('Reading promises')
        self.promises = []

        with open(self.promise_file, 'r') as csvfile:
            for row in csv.DictReader(csvfile):
                self.promises.append(row)
