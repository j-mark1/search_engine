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

def term_of(line):
    return line.split("\t", 1)[0]

def merge_partials(partials, num_docs):
    handles = [open(path, encoding="utf-8") for path in partials]
    merged_lines = heapq.merge(*handles, key=term_of)
    squared_lengths = [0.0] * num_docs
    num_terms = 0
    with open(INDEX_DIR / "postings.txt", "w", encoding="utf-8") as postings_out, open(INDEX_DIR / "lexicon.tsv", "w", encoding="utf-8") as lexicon_out:
        for term, lines in itertools.groupby(merged_lines, key=term_of):
            postings = []
            for line in lines:
                postings.extend(line.rstrip("\n").split("\t", 1)[1].split(" "))
            idf = math.log10(num_docs / len(postings))
            weighted = []
            for posting in postings:
                doc, count = posting.split(":")
                weight = (1 + math.log10(int(count))) * idf
                squared_lengths[int(doc)] += weight * weight
                weighted.append(f"{doc}:{weight:.4f}")
            lexicon_out.write(f"{term}\t{len(postings)}\t{postings_out.tell()}\n")
            postings_out.write(f"{term}\t{' '.join(weighted)}\n")
            num_terms += 1
    for handle in handles:
        handle.close()
    for path in partials:
        path.unlink()
    with open(INDEX_DIR / "norms.txt", "w", encoding="utf-8") as norms_out:
        norms_out.writelines(f"{math.sqrt(total):.6f}\n" for total in squared_lengths)
    return num_terms

def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python indexer.py /path/to/DEV")
    INDEX_DIR.mkdir(exist_ok=True)
    files = sorted(Path(sys.argv[1]).rglob("*.json"))
    print(f"Indexing {len(files):,} files...")
    start = time.time()

    partials, num_docs = build_partials(files)
    print(f"Merging {len(partials)} partial indexes...")
    num_terms = merge_partials(partials, num_docs)

    size_kb = sum(f.stat().st_size for f in INDEX_DIR.iterdir()) / 1024
    print(f"Done in {time.time() - start:.0f}s: {num_docs:,} unique pages, {num_terms:,} unique terms, {size_kb:,.0f} KB on disk")

if __name__ == "__main__":
    main()
