from pathlib import Path
from indexing.indexer import ReverseIndexer
import time
import sys

already_restored = False
ri = ReverseIndexer("data/DEV", "out")

# Run a search with the given query. If no pages have been indexed, run indexer and index all documents.
# Otherwise, skip and go straight to search.
# @ str query: the query being searched.
# => return: Dictionary of documents that matches the query in the following format: {docId: {"file": str, "tfidf": float}, ...}
def run_search(query):
    global already_restored
    global ri

    if not already_restored:
        # If documents have all been indexed and merged into a reversed index, restore index stats
        # and use the existing index. Restore only once for efficiency.
        if not ri.restore():
            # Failed to restore. No save file exists.
            raise IndexError("No index found.")
        already_restored = True

    start_time = time.perf_counter() # Time how long it takes to get search results
    results = ri.query(query, 5)
    end_time = time.perf_counter()
    print(f"\033[92m Elapsed time: {end_time - start_time:.4f} seconds\033[0m")
    return results