#!/usr/bin/env python
# -*- coding: utf-8 -*-

from optparse import OptionParser

import sys
import json
import csv

op = OptionParser()
(opts, args) = op.parse_args()

if len(args) != 2:
  op.error('USAGE: consolidate.py promises.csv similarities.json')
  sys.exit(1)


promise_ids = []
similarities = [];

with open(args[0], 'r') as csvfile:
  reader = csv.DictReader(csvfile)
  for row in reader:
    promise_ids.append(int(row['id']))

with open(args[1]) as jsonfile:
  similarities = json.load(jsonfile)

result = []

for sim in similarities:
  result.append({
    "id": promise_ids[sim['index']],
    "related": [{
      "id": promise_ids[related['index']],
      "score": related['score']
    } for related in sim['related'] if related['index'] != sim['index']]
  })

print(json.dumps(result))