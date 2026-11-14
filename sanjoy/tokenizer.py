import re
import warnings
from collections import Counter
from functools import lru_cache
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning, XMLParsedAsHTMLWarning
from nltk.stem import PorterStemmer

# parsing XML feeds as HTML is fine
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
IMPORTANT_TAG_WEIGHTS = {"title": 4, "h1": 3, "h2": 2, "h3": 2, "b": 1, "strong": 1}

_stemmer = PorterStemmer()

@lru_cache(maxsize=None)
def stem(word):
    return _stemmer.stem(word)


def tokenize_text(text):
    return [stem(word) for word in TOKEN_PATTERN.findall(text.lower())]

def weighted_term_counts(html):
    soup = BeautifulSoup(html, "lxml")
    for junk in soup(["script", "style", "noscript"]):
        junk.decompose()

    counts = Counter(tokenize_text(soup.get_text(" ")))
    for tag_name, extra_weight in IMPORTANT_TAG_WEIGHTS.items():
        for tag in soup.find_all(tag_name):
            for term in tokenize_text(tag.get_text(" ")):
                counts[term] += extra_weight
    return counts
