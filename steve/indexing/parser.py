from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning, XMLParsedAsHTMLWarning
import warnings
from collections import Counter, defaultdict
import re

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Read the stopwords file and create a set of all stopwords to remove from tokenization
# @ str path: Path of the stopwords file
# => return: frozenset() of all stopwords
def load_stopwords(path="indexing/stopwords.txt"):
    words = set()

    with open(path, encoding="utf-8") as file:
        for line in file:
            words.update(re.findall(r"\S+", line.lower()))
    return frozenset(words)

STOPWORDS = load_stopwords()

# Remove the stopwords from the collection of tokens
# @ Counter tokens: A Counter object of all tokens and their frequencies
# => return: {str token: int frequency, ...}
def remove_stopwords(tokens):
    cleaned_tokens = {}
    
    for word in tokens:
        if word not in STOPWORDS:
            cleaned_tokens[word] = tokens[word]

    return cleaned_tokens

# Tokenize the content
# @ str page_response_content: A string of the whole html page content
# => return (Counter tokens, defaultdict positions), a tuple of all the tokens and a dict of their corresponding positions on the page
def tokenize(page_response_content):
    try:
        soup = BeautifulSoup(page_response_content, "lxml")
        all_individual_tokens = re.findall(r"\w+", soup.get_text(separator=" ").lower())
    except (Exception):
        # If parse error, try again with html.parser
        try:
            soup = BeautifulSoup(page_response_content, "html.parser")
            all_individual_tokens = re.findall(r"\w+", soup.get_text(separator=" ").lower())
        except Exception:
            return Counter(), {}  # Skip completely if it's unparseable

    del soup # Delete after use to reuse some memory

    tokens = Counter(all_individual_tokens)
    positions = defaultdict(list)
    for i, token in enumerate(all_individual_tokens):
        if token not in STOPWORDS:
            positions[token].append(i)
    
    del all_individual_tokens # Delete after use to reuse some memory

    positions = {token: ",".join(map(str, pos)) for token, pos in positions.items()}

    return tokens, positions