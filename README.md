# hdo-promise-similarity

Compute the cosine similarity of Norwegian political party programs.

# Usage
Install the [Oslo Bergen Tagger][1] with dependencies into `./obt`

    ./install_tagger.sh  # Should work on MacOS and Debian/Ubuntu

Install and run

    python3 -m venv venv
    . venv/bin/activate
    pip install -r requirements.txt
    python promise_similarity  # using OBT in ./obt by default

[1]: https://github.com/noklesta/The-Oslo-Bergen-Tagger
