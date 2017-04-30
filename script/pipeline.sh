#!/bin/bash

set -e

echo -n "Tagging promises…"

script/tag-csv.py \
  --text-column body \
  --obt-path ~/src/The-Oslo-Bergen-Tagger \
  --only-lemmas \
  data/promises.csv > data/lemmas.ndjson

echo "done."
echo -n "Calculating cosine similarities…"

script/cosine-similarity.py \
  data/lemmas.ndjson > data/similarities.json

echo "done."
echo -n "Consolidating data…"

script/consolidate.py \
  data/promises.csv data/similarities.json
  
echo "done."