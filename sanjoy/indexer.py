import heapq
import itertools
import json
import math
import sys
import time
from multiprocessing import Pool
from pathlib import Path
from urllib.parse import urldefrag

from tokenizer import weighted_term_counts

INDEX_DIR = Path(__file__).parent / "index"
DOCS_PER_PARTIAL = 10_000

def parse_page(path):
    try:
        with open(path, encoding="utf-8") as file:
            page = json.load(file)
        url = urldefrag(page["url"])[0]
        if any(char in url for char in "\t\r\n"):
            return url, {}
        return url, dict(weighted_term_counts(page["content"]))
    except (OSError, ValueError, KeyError, TypeError, RecursionError, AssertionError) as error:
        print(f"  skipped {path.name}: {error!r}", file=sys.stderr)
        return str(path), {}
