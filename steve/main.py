from pathlib import Path
import json
from parser import *

folder_path = Path("sample")

files = [file for file in folder_path.iterdir() if file.is_file()]

for file in files:
    with open(file, 'r', encoding='utf-8') as file:
        data = json.load(file)
        tokens = tokenize(data["content"])
        print(remove_stopwords(tokens))