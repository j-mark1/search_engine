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

def write_partial(index, number):
    path = INDEX_DIR / f"partial_{number}.txt"
    with open(path, "w", encoding="utf-8") as out:
        for term in sorted(index):
            postings = " ".join(f"{doc}:{count}" for doc, count in index[term])
            out.write(f"{term}\t{postings}\n")
    print(f"  wrote {path.name} ({len(index):,} terms)")
    return path

def build_partials(files):
    index = {}
    partials = []
    seen_urls = set()
    doc_id = 0
    with Pool() as pool, open(INDEX_DIR / "docs.tsv", "w", encoding="utf-8") as docs_out:
        for url, counts in pool.imap(parse_page, files, chunksize=32):
            if url in seen_urls or not counts:
                continue
            seen_urls.add(url)
            docs_out.write(f"{doc_id}\t{url}\n")
            for term, count in counts.items():
                index.setdefault(term, []).append((doc_id, count))
            doc_id += 1
            if doc_id % DOCS_PER_PARTIAL == 0:
                partials.append(write_partial(index, len(partials)))
                index = {}
    if index:
        partials.append(write_partial(index, len(partials)))
    return partials, doc_id
