from pathlib import Path
import json
from parser import *
import heapq

class ReverseIndexer:
    def __init__(self):
        self.doc_finder = {}
        self.word_finder = {}
        self.all_words = {}
        folder_path = Path("sample")
        self.files = [file for file in folder_path.iterdir() if file.is_file()]
        self.block = 0

    def create_index(self):
        doc_id = 0

        # Have document indexer file ready
        with open("document_ids.index", 'w', encoding='utf-8') as doc_id_file:
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
                        self.create_new_word_block()

                    # Document Indexer - Index docs and doc_ids
                    self.doc_finder[doc_id] = doc_id_file.tell() # Store byte offset
                    doc_id_file.write(f"{doc_id}|{file.name}\n")  

                doc_id += 1  
        
        # Flush out rest of words if any are leftover
        if len(self.all_words) > 0:
            self.create_new_word_block()

        # Merge
        self.word_finder = self.merge_all_blocks()
     
    def create_new_word_block(self):
        # Word Indexer
        with open(f"words{self.block}.index", 'w', encoding='utf-8') as word_block:
            for word in sorted(self.all_words.keys()):
                self.word_finder[word] = word_block.tell() # Store byte offset
                word_block.write(f"{word}|{','.join(self.all_words[word])}\n")
        self.all_words = {}
        self.block += 1

    def merge_all_blocks(self):
        block_files = []
        for i in range(self.block):
            block_files.append(f"words{i}.index")

        file_handles = [open(f, "r", encoding="utf-8") for f in block_files]
        
        word_finder = {}  # term: byte_offset
        
        # heapq.merge streams lines across all files in sorted alphabetical order
        sorted_lines = heapq.merge(*file_handles)
        
        with open("words_index.index", "w", encoding="utf-8") as out_file:
            current_term = None
            current_postings = []
            
            for line in sorted_lines:
                line = line.strip()
                if not line:
                    continue
                    
                term, postings_str = line.split("|", 1)
                
                # If we hit a new word, write out the accumulated postings of the previous word
                if term != current_term:
                    if current_term is not None:
                        # 1. Capture byte offset BEFORE writing
                        offset = out_file.tell()
                        word_finder[current_term] = offset

                        # 2. Write the combined term and postings
                        out_file.write(f"{current_term}|{','.join(current_postings)}\n")
                    
                    # Reset tracking for new word
                    current_term = term
                    current_postings = [postings_str]
                else:
                    # Same word found in another block file: append its postings
                    current_postings.append(postings_str)
                    
            # Write the final remaining word after the loop ends
            if current_term is not None:
                offset = out_file.tell()
                word_finder[current_term] = offset
                out_file.write(f"{current_term}|{','.join(current_postings)}\n")
                
        # Close all block file handles
        for f in file_handles:
            f.close()
            
        return word_finder

    def find_related_docs(self, word):
        with open("words_index.index", "w", encoding="utf-8") as words_index:
            w_offset = self.word_finder[word]
            words_index.seek(w_offset)

            line = words_index.readline()
            postings = line.split("|")[1]
            posting_list = postings.split(",")

            with open("document_ids.index", "w", encoding="utf-8") as doc_index:
                for posting in posting_list:
                    doc_id = posting.split(":")[0]
                    d_offset = self.doc_finder[doc_id]
                    doc_index.seek(d_offset)
                    line = doc_index.readline()
                    print(line.split("|")[1])
