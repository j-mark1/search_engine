from bs4 import BeautifulSoup
from collections import Counter
import re

def tokenize(page_response_content):
    soup = BeautifulSoup(page_response_content, "lxml")

    tokens = Counter(re.findall(r"\w+", soup.get_text(separator=" ").lower()))

    return tokens

def load_stopwords(path="stopwords.txt"):
    words = set()
    with open(path, encoding="utf-8") as file:
        for line in file:
            words.update(tokenize(line))
    return frozenset(words)

STOPWORDS = load_stopwords()

def remove_stopwords(tokens):
    return Counter(word for word in tokens if word not in STOPWORDS)
