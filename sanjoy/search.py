import heapq
import math
import sys
import time
from pathlib import Path

from tokenizer import tokenize_text

INDEX_DIR = Path(__file__).parent / "index"
RESULTS_TO_SHOW = 5

class SearchEngine:
    def __init__(self):
        self.lexicon = {}
        with open(INDEX_DIR / "lexicon.tsv", encoding="utf-8") as file:
            for line in file:
                term, df, offset = line.split("\t")
                self.lexicon[term] = (int(df), int(offset))
        with open(INDEX_DIR / "docs.tsv", encoding="utf-8") as file:
            self.urls = [line.rstrip("\n").split("\t", 1)[1] for line in file]
        with open(INDEX_DIR / "norms.txt", encoding="utf-8") as file:
            self.norms = [float(line) or 1.0 for line in file]
        self.postings_file = open(INDEX_DIR / "postings.txt", "rb")

    def read_postings(self, term):
        self.postings_file.seek(self.lexicon[term][1])
        line = self.postings_file.readline().decode("utf-8")
        postings = {}
        for item in line.rstrip("\n").split("\t", 1)[1].split(" "):
            doc, weight = item.split(":")
            postings[int(doc)] = float(weight)
        return postings

    def search(self, query):
        terms = list(dict.fromkeys(tokenize_text(query)))
        if not terms or any(term not in self.lexicon for term in terms):
            return 0, []
        terms.sort(key=lambda term: self.lexicon[term][0])

        scores = None
        for term in terms:
            query_weight = math.log10(len(self.urls) / self.lexicon[term][0])
            postings = self.read_postings(term)
            if scores is None:
                scores = {doc: weight * query_weight for doc, weight in postings.items()}
            else:
                scores = {doc: score + postings[doc] * query_weight for doc, score in scores.items() if doc in postings}
            if not scores:
                return 0, []

        cosine = {doc: score / self.norms[doc] for doc, score in scores.items()}
        best = heapq.nlargest(RESULTS_TO_SHOW, cosine.items(), key=lambda item: item[1])
        return len(cosine), [(self.urls[doc], score) for doc, score in best]