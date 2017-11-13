import os
import re
from subprocess import Popen, PIPE


class ObtTagger:
    def __init__(self, obt_path, promises):
        self.obt_path = obt_path
        self.promises = promises

    def tag(self):
        tmpfile = '/tmp/hdo-promise-similarity-tagging.txt'
        separator = '----'  # separator chosen can affect tagging! e.g. ____

        with open(tmpfile, 'w') as out:
            for row in self.promises:
                out.write(separator + ' ' + row['body'] + '\n')

        tagbm = os.path.join(self.obt_path, 'tag-bm.sh')
        proc = Popen([tagbm, tmpfile], stdout=PIPE, stderr=open(os.devnull, 'w'))

        result = []
        current_word = None
        current_sentence = None

        while True:
            line = proc.stdout.readline().decode('utf-8')

            if line != '':

                word = re.match(r'<word>(.+)</word>$', line)

                if word:
                    group = word.group(1)

                    if group == separator:
                        if current_sentence:
                            result.append(current_sentence)
                        current_sentence = []
                    else:
                        current_word = {'word': group}
                        current_sentence.append(current_word)

                tag = re.match(r'\t"(.+?)" (.+)$', line)

                if tag:
                    (lemma, tags) = (tag.group(1), tag.group(2).split(' '))

                    if lemma != separator:
                        current_word['lemma'] = tag.group(1)
                        current_word['tags'] = tag.group(2).split(' ')
            else:
                break

        if current_sentence:
            result.append(current_sentence)

        return [
            [word['lemma'] for word in sentence] for sentence in result
        ]
