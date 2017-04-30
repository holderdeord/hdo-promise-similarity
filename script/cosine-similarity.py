#!/usr/bin/env python
# -*- coding: utf-8 -*-

from optparse import OptionParser
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

import sys
import json

op = OptionParser()

(opts, args) = op.parse_args()

if len(args) == 0:
    op.error('no file given')
    sys.exit(1)

data = []

with open(args[0], 'r') as ndjsonfile:
  for line in ndjsonfile.readlines():
    data.append(' '.join(json.loads(line)))


tfidf = TfidfVectorizer().fit_transform(data);
result = []

for index in range(len(data)):
  cosine_similarities = linear_kernel(tfidf[index:index+1], tfidf).flatten()
  related_docs_indices = cosine_similarities.argsort()[:-10:-1]
  scores = cosine_similarities[related_docs_indices]

  result.append({
    "index": index,
    "related": [{
      "index": index, 
      "score": score, 
      "text": data[index]
    } for (index, score) in zip(related_docs_indices, scores)]
  })

print(json.dumps(result))