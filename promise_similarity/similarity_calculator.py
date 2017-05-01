from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import numpy as np


class SimilarityCalculator():

    def __init__(self, docs, top=None, threshold=None, stop_words=None):
        self.docs = docs
        self.top = top
        self.threshold = threshold
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 1),
            # analyzer=lambda s: s.lower().split(), # our docs are
            # pre-tokenized by OBT
            stop_words=stop_words
        )

        if not top and not threshold:
            raise ValueError("must provide either 'top' or 'threshold'")

    def get(self):
        tfidf = self.vectorizer.fit_transform(self.docs)
        cosine_similarities = linear_kernel(tfidf)
        result = []

        for index in range(len(self.docs)):
            all_scores = cosine_similarities[index]

            if self.top:
                related_docs_indices = all_scores.argsort()[:-self.top:-1]
                scores = all_scores[related_docs_indices]
            elif self.threshold:
                related_docs_indices = np.nonzero(
                    all_scores > self.threshold)[0]
                scores = all_scores[related_docs_indices]

            related = [
                {
                    "index": idx,
                    "score": score,
                    "text": self.docs[idx]
                } for (idx, score) in zip(related_docs_indices, scores) if idx != index
            ]

            if len(related) > 0:
                result.append({
                    "index": index,
                    "related": related
                })

        return result
