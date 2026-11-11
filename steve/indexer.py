from pathlib import Path
import json
from parser import *
import heapq
import json

class ReverseIndexer:
    def __init__(self, data_path, out_path):
        self.doc_finder = {}
        self.word_finder = {}
        self.all_words = {}
        folder_path = Path(data_path)
        self.files = [file for file in folder_path.rglob("*") if file.is_file()]
        self.output_path = out_path
        self.block = 0

        self.doc_count = 0
        self.unique_words_count = 0

    def create_index(self):
        doc_id = 0

        # Have document indexer file ready
        with open(f"{self.output_path}/document_ids.index", 'w', encoding='utf-8') as doc_id_file:
            for file in self.files:
                self.doc_count += 1 # For report
                document_tokens = None

                with open(file, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    tokens = tokenize(data["content"]) # returns Counter
                    total_freq = tokens.total()

                    document_tokens = remove_stopwords(tokens)

                    for token in document_tokens:
                        if token not in self.all_words:
                            self.all_words[token] = []

                        # Format: word|doc_id:frequency:term_ratio, ...
                        self.all_words[token].append(f"{doc_id}:{document_tokens[token]}:{round(document_tokens[token]/total_freq, 2)}")

                    # Create new block
                    if len(self.all_words) > 10000:
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
        with open(f"{self.output_path}/words{self.block}.index", 'w', encoding='utf-8') as word_block:
            for word in sorted(self.all_words.keys()):
                self.word_finder[word] = word_block.tell() # Store byte offset
                word_block.write(f"{word}|{','.join(self.all_words[word])}\n")
        self.all_words = {}
        self.block += 1

    def merge_all_blocks(self):
        block_files = []
        for i in range(self.block):
            block_files.append(f"{self.output_path}/words{i}.index")

        file_handles = [open(f, "r", encoding="utf-8") for f in block_files]
        
        word_finder = {}  # term: byte_offset
        
        # heapq.merge streams lines across all files in sorted alphabetical order
        sorted_lines = heapq.merge(*file_handles, key=lambda line: line.split("|", 1)[0])
        
        with open(f"{self.output_path}/words_index.index", "w", encoding="utf-8") as out_file:
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
                        self.unique_words_count += 1 # For report

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

    def _find_related_docs(self, word):
        # Word does not exist in any document
        if word not in self.word_finder:
            return []

        with open(f"{self.output_path}/words_index.index", "r", encoding="utf-8") as words_index:
            w_offset = self.word_finder[word]
            words_index.seek(w_offset)

            line = words_index.readline()
            postings = line.split("|")[1]
            posting_list = postings.split(",")
            related_docs = []

            with open("document_ids.index", "r", encoding="utf-8") as doc_index:
                for posting in posting_list:
                    doc_id = posting.split(":")[0]
                    
                    d_offset = self.doc_finder[int(doc_id)]
                    doc_index.seek(d_offset)
                    line = doc_index.readline()
                    # Format: docID | url
                    related_docs.append(line.split("|")[1])
            
        return related_docs

    def query(self, query):
        scores = {}
        words = query.lower().split()

        for word in query:
            related_docs = _find_related_docs(word)

            # Word does not exist in any document
            if len(related_docs) == 0:
                continue
        
            idf = math.log(total_docs / (1 + len(related_docs)))

            # Construct tfidf and do the rest...



    def print_report(self):
        size = Path(f"{self.output_path}/words_index.index").stat().st_size/1024

        print(f"""
+----------------------+----------------------+
| Metric               | Value                |
+----------------------+----------------------+
| Num of docs          | {self.doc_count:<20} |
| Num of unique tokens | {self.unique_words_count:<20} |
| Total size           | {f'{size}KB':<20} |
+----------------------+----------------------+
        """)

    def save(self):
        # Save structure data to restore later if needed, mainly for debugging
        with open(f"{self.output_path}/save.index", "w", encoding="utf-8") as save:
            all_data = [
                self.doc_finder,
                self.word_finder,
                self.all_words,
                self.block,
                self.doc_count,
                self.unique_words_count
            ]
            json.dump(all_data, save, indent=4)
    

    def restore(self):
        if Path(f"{self.output_path}/save.index").is_file():
            with open(f"{self.output_path}/save.index", "r", encoding="utf-8") as save:
                loaded_file = json.load(save)
                self.doc_finder = loaded_file[0]
                self.word_finder = loaded_file[1]
                self.all_words = loaded_file[2]
                self.block = loaded_file[3]
                self.doc_count = loaded_file[4]
                self.unique_words_count = loaded_file[5]
            return True
        return False