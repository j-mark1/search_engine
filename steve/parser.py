from bs4 import BeautifulSoup
from collections import Counter
import re

def tokenize(page_response_content):
    try:
        soup = BeautifulSoup(page_response_content, "lxml")
        tokens = Counter(re.findall(r"\w+", soup.get_text(separator=" ").lower()))
    except (ValueError, Exception):
        # If parse error, try again with html.parser
        try:
            soup = BeautifulSoup(page_response_content, "html.parser")
            tokens = Counter(re.findall(r"\w+", soup.get_text(separator=" ").lower()))
        except Exception:
            return Counter()  # Skip completely if it's unparseable

    return tokens

def load_stopwords(path="stopwords.txt"):
    words = set()
    with open(path, encoding="utf-8") as file:
        for line in file:
            words.update(tokenize(line))
    return frozenset(words)

STOPWORDS = load_stopwords()

def remove_stopwords(tokens):
    cleaned_tokens = {}
    
    for word in tokens:
        if word not in STOPWORDS:
            cleaned_tokens[word] = tokens[word]

    return cleaned_tokens
