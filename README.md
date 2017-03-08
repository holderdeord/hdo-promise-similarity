# hdo-promise-similarity

Compute the cosine similarity of Norwegian political party programs.

# Usage

Install the [Oslo Bergen Tagger][1], then

    pip install -r requirements.txt

    script/download.sh

    script/tag-csv.py \
      --text-column body \
      --obt-path /path/to/oslo-bergen-tagger \
      data/promises.csv

# Process

* Fetch promises
* Lemmatize/tag using the OBL tagger (+ possibly remove stop words)
* Frequency matrix -> TF-IDF scores
* Compare cosine similarity

Set a similairty threshold, and build an id map that can be visualized/analyzed:

```json
{
  "1": {
    "2": 0.978,
    "3": 0.985
  }
}

```

[1]: https://github.com/noklesta/The-Oslo-Bergen-Tagger