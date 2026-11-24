from pathlib import Path
from indexing.indexer import ReverseIndexer
import time
import sys

already_restored = False
ri = ReverseIndexer("data/DEV", "out")

def print_query_results(search, results):
    print(f"* Query Results for {search}:")

    for result in results:
        docID = result[0]
        url = result[1][0].strip()
        tfidf = result[1][1]

        print(
f"""
 Doc ID: {docID}
 path: {url}
 TFIDF Score:{tfidf}"""
        )
    print("+---------------------------------------\n")

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
    print(f"Elapsed time: {end_time - start_time:.4f} seconds")
    return results


if __name__ == "__main__":
    # Set the directory you want to search
    target_dir = Path("./steve")

    for file_path in target_dir.glob("*.index"):
        if file_path.is_file():  # Ensure it's a file and not a subfolder
            try:
                file_path.unlink()
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

    ri = ReverseIndexer("data/DEV", "out")
    if not ri.restore():
        ri.create_index()
        ri.save()
    ri.print_report()

    args = sys.argv[1:]
    searches = ["cristina lopes", "machine learning", "ACM", "master of software engineering"]
    if not(args is None or len(args) == 0):
        searches = [" ".join(args)]

    for search in searches:
        start_time = time.perf_counter()
        results = ri.query(search, 5)
        end_time = time.perf_counter()
        print(f"Elapsed time: {end_time - start_time:.4f} seconds")
        print_query_results(search, results)