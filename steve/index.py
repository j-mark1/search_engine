from indexing.indexer import ReverseIndexer
from pathlib import Path
import time

# Delete all index blocks in the ./out folder to restart the indexing process.
# => return: None
def clear_existing_index():
    target_dir = Path("./out")

    for file_path in target_dir.glob("*.index"):
        if file_path.is_file():  # Ensure it's a file and not a subfolder
            try:
                file_path.unlink()
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

# Create a new index and save memory dicts as well as statistics to disk
if __name__ == "__main__":
    clear_existing_index()
    print("All indexes cleared")

    start_time = time.perf_counter() # Time how long it takes to build reverse index
    ri = ReverseIndexer("data/DEV", "out")
    ri.create_index()
    end_time = time.perf_counter()
    print(f"Elapsed time: {end_time - start_time:.4f} seconds")
    ri.save()
    ri.print_report()