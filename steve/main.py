from pathlib import Path
from indexer import ReverseIndexer

# Set the directory you want to search
target_dir = Path("./steve")

for file_path in target_dir.glob("*.index"):
    if file_path.is_file():  # Ensure it's a file and not a subfolder
        try:
            file_path.unlink()
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

ri = ReverseIndexer()
ri.create_index()
ri.find_related_docs("absent")