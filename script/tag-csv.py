#!/usr/bin/env python
# -*- coding: utf-8 -*-

from optparse import OptionParser

import sys
import csv
import json
import re
import os

from subprocess import Popen, PIPE

op = OptionParser()
op.add_option('--text-column',
              type='string',
              action='store',
              dest='text_column',
              help='What column to read text from')
op.add_option('--obt-path',
              type='string',
              action='store',
              dest='obt_path',
              help='Path to Oslo-Bergen-Tagger')
op.add_option('--only-lemmas',
              action='store_true',
              dest='only_lemmas',
              help='Print just the "lemmatized" version of sentences')
op.add_option('--ndjson',
              action='store_true',
              dest='ndjson',
              help='Print newline-delimited JSON')

(opts, args) = op.parse_args()

tmpfile = '/tmp/tag-csv-tmp.txt'
separator = '----' # separator chosen can affect tagging! e.g. ____

if not opts.text_column:
    op.error('must set --text-column')
    sys.exit(1)

if not opts.obt_path:
    op.error('must set --obt-path')
    sys.exit(1)

if len(args) == 0:
    op.error('no file given')
    sys.exit(1)

with open(args[0], 'r') as csvfile:
    reader = csv.DictReader(csvfile)

    with open(tmpfile, 'w') as out:
        for row in reader:
            try:
              text = row[opts.text_column];
              out.write(separator + ' ' + text + '\n')
            except Exception as e:
              print(json.dumps(text))
              raise

tagbm = os.path.join(opts.obt_path, 'tag-bm.sh')
proc = Popen([tagbm, tmpfile], stdout=PIPE, stderr= open(os.devnull, 'w'))

result = []
current_word = None
current_sentence = None

while True:
    line = proc.stdout.readline()

    if line != '':
        # print line.rstrip()

        word = re.match(r'<word>(.+)</word>$', line)

        if word:
            group = word.group(1)

            if group == separator:
                if current_sentence:
                    result.append(current_sentence)
                current_sentence = []
            else:
                current_word = {'word': group }
                current_sentence.append(current_word)

        tag = re.match(r'\t"(.+?)" (.+)$', line)

        if tag:
            (lemma, tags) = (tag.group(1), tag.group(2).split(' '))

            if lemma != separator:
                current_word['lemma'] = tag.group(1)
                current_word['tags'] = tag.group(2).split(' ')
    else:
        break

if opts.only_lemmas:
    for sentence in result:
        lemmas = [word['lemma'] for word in sentence]
        print(json.dumps(lemmas))
elif opts.ndjson:
    for sentence in result:
        print(json.dumps(result))
else:
    print(json.dumps(result))