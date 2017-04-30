from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


class SimilarityCalculator():

    def __init__(self, docs):
        self.docs = docs

    def get(self):
        tfidf = TfidfVectorizer().fit_transform(self.docs)
        result = []

        for index in range(len(self.docs)):
            cosine_similarities = linear_kernel(
                tfidf[index:index + 1], tfidf
            ).flatten()

            related_docs_indices = cosine_similarities.argsort()[:-10:-1]
            scores = cosine_similarities[related_docs_indices]

            result.append({
                "index": index,
                "related": [{
                    "index": index,
                    "score": score,
                    "text": self.docs[index]
                } for (index, score) in zip(related_docs_indices, scores)]
            })

        return result
