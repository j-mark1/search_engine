from pathlib import Path
import json
from parser import *

class ReverseIndexer:
    def __init__(self):
        self.doc_finder = {}
        self.word_finder = {}
        self.all_words = {}
        folder_path = Path("sample")
        self.files = [file for file in folder_path.iterdir() if file.is_file()]
        self.block = 0

    def run(self):
        doc_id = 0
        for file in self.files:
            document_tokens = None

            with open(file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                tokens = tokenize(data["content"]) # returns Counter
                document_tokens = remove_stopwords(tokens)

                for token in document_tokens:
                    if token not in self.all_words:
                        self.all_words[token] = []
                    self.all_words[token].append(f"{doc_id}:{document_tokens[token]}")

                # Create new block
                if len(self.all_words) > 300:
                    self.create_new_block()

                # Document Indexer - Index docs and doc_ids
                with open("document_ids.txt", 'a', encoding='utf-8') as doc_id_file:
                    self.doc_finder[doc_id] = doc_id_file.tell() # Store byte offset
                    doc_id_file.write(f"{doc_id}|{file.name}\n")  

            doc_id += 1  
     
    def create_new_block(self):
        # Word Indexer
        with open(f"words{self.block}.txt", 'w', encoding='utf-8') as word_block:
            for word in sorted(self.all_words.keys()):
                self.word_finder[word] = word_block.tell() # Store byte offset
                word_block.write(f"{word}|{self.word_finder[word]}\n")
        self.all_words = {}
        self.block += 1


ri = ReverseIndexer()
ri.run()