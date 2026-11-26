from pathlib import Path
import json
from indexing.parser import *
import heapq
import json
import math
import psutil
import sys

# Tracks and estimates the usage of memory to adjust to different machine requirements. 
class MemoryUsage():
    def __init__(self):
        MAX_INDEX_SIZE = 256 * 1024 * 1024  # 256 MB index threshold, impose limit to ensure not just 1 partial index is made, even if machine can hold it all

        self.available_memory = psutil.virtual_memory().available * 0.6
        self.available_memory = min(
            self.available_memory,
            MAX_INDEX_SIZE
        )
        self.current_memory = 0
        self.prev_index_size = 0

    # Saves the shallow size of the current partial_index dictionary before any new terms
    # from the next document are added.
    # @ dict partial_index: Current in-memory dictionary containing the tokens and postings
    # => return None
    def set_prev_index_size(self, partial_index):
        self.prev_index_size = sys.getsizeof(partial_index)
        
    # Update the amount of memory used by storing the sizes of the partial_index, key, and value.
    # The amount added serves as a general estimate of the memory being used up.
    # @ dict partial_index: Current in-memory dictionary containing the tokens and postings
    # @ str key: The key that is being added to the partial_index
    # @ str value: The value that is being added to the partial_index
    # => return None
    def update_memory_usage(self, partial_index, key, value):
        self.current_memory += sys.getsizeof(key)
        self.current_memory += sys.getsizeof(value)
        self.current_memory += sys.getsizeof(partial_index) - self.prev_index_size

    # Check whether the amount of memory used is over the memory limit threshold before flushing.
    # => return boolean
    def memory_threshold_surpassed(self):
        if self.current_memory >= self.available_memory:
            self.reset()
            return True
        return False

    # Reset memory tracking
    # => return None
    def reset(self):
        self.current_memory = 0
        self.prev_index_size = 0


# Creates, manages, and provides the query processing of the search engine's reversed index.
class ReverseIndexer:
    def __init__(self, data_path, out_path):
        self.doc_finder = {}
        self.word_finder = {}
        self.all_words = {}
        folder_path = Path(data_path)
        self.files = [file for file in folder_path.rglob("*") if file.is_file()] # Get all json files from the folder path provided
        self.output_path = out_path
        self.block = 0

        self.doc_count = 0 # Track total number of documents indexed
        self.unique_words_count = 0 # Track total number of unique words

        self.words_index = None
        self.docs_index = None

    # Create a reverse index by first creating partial indexes and then merging them together.
    # => return: None
    def create_index(self):
        doc_id = 0
        memory = MemoryUsage()

        # Have document_id index file ready. Create if it does not exist.
        with open(f"{self.output_path}/document_ids.index", 'w', encoding='utf-8') as doc_id_file:
            for file in self.files:
                self.doc_count += 1
                document_tokens = None

                with open(file, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    tokens, positions = tokenize(data["content"]) # returns Counter containing tokens and count
                    total_freq = tokens.total()

                    document_tokens = remove_stopwords(tokens)

                    # Store tokens and related term information in memory until memory threshold is passed.
                    for token in document_tokens:
                        if token not in self.all_words:
                            self.all_words[token] = []

                        posting = f"{doc_id}:{document_tokens[token]}:{round(document_tokens[token]/total_freq, 4)}:{positions[token]}"
                        memory.set_prev_index_size(self.all_words)

                        # Format: word|doc_id:frequency:term_ratio:positions, ...
                        self.all_words[token].append(posting)
                        memory.update_memory_usage(self.all_words, token, posting)

                    # If memory threshold is passed, write block in disk and create new block
                    if memory.memory_threshold_surpassed():
                        self.create_new_word_block()

                    # Document Index File - Index and write docs and doc_ids into disk
                    self.doc_finder[str(doc_id)] = doc_id_file.tell() # Store byte offset
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
                word_block.write(f"{word}|{';'.join(self.all_words[word])}\n")
        self.all_words = {}
        self.block += 1
        print("New block created.")

    def merge_all_blocks(self):
        block_files = []
        for i in range(self.block):
            block_files.append(f"{self.output_path}/words{i}.index")

        file_handles = [open(f, "r", encoding="utf-8") for f in block_files]
        
        word_finder = {}  # term: byte_offset
        
        # heapq.merge applies a k-way merge algorithm to sort all the lines across all files
        # based on the word in alphabetical order
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
                        out_file.write(f"{current_term}|{';'.join(current_postings)}\n")
                    
                    # Reset tracking for new word
                    current_term = term
                    current_postings = [postings_str]
                else:
                    # Same word found in another block file: append its postings
                    current_postings.append(postings_str)
                    
            # Write the final remaining word after the loop ends
            if current_term is not None:
                self.unique_words_count += 1 # For report

                offset = out_file.tell()
                word_finder[current_term] = offset
                out_file.write(f"{current_term}|{';'.join(current_postings)}\n")
                
        # Close all block file handles
        for f in file_handles:
            f.close()
            
        return word_finder

    def _find_related_docs(self, word):
        # Clean query
        word = re.sub(r"[^a-z0-9]", "", word.lower())

        # Word does not exist in any document
        if word not in self.word_finder:
            return []

        w_offset = self.word_finder[word]
        self.words_index.seek(w_offset)

        line = self.words_index.readline()

        # Format: word|doc_id:frequency:term_ratio:positions; ...
        postings = line.split("|")[1]
        posting_list = postings.split(";")
        
        return posting_list
    
    def _get_posting_info(self, posting_list):
        for posting in posting_list:
            split_posting = posting.split(":")
            doc_id = split_posting[0]
            frequency = int(split_posting[1])
            # tf_ratio = float(split_posting[2])
            positions = list(map(int, split_posting[3].split(",")))
            
            # Format: related_docs = {docID: [log tf ratio, [positions,...]]}
            info = [1 + math.log(frequency), positions]
            yield doc_id, info

    def query(self, query, number_of_results):
        # Open the reversed index and doc index throughout entire query
        self.words_index = open(f"{self.output_path}/words_index.index", "r", encoding="utf-8")
        self.doc_index = open(f"{self.output_path}/document_ids.index", "r", encoding="utf-8")

        scores = {}
        words = query.lower().split()

        prev_related_doc_ids = None
        related_doc_ids = None
        positions = {}

        for i, word in enumerate(words):        
            posting_list = self._find_related_docs(word)
            idf = math.log(self.doc_count / (1 + len(posting_list)))

            for doc_id, info in self._get_posting_info(posting_list):
                positional_score = 0

                # Progressively check that the words appear next to each other in the same docs.
                # If so, increase score.
                if doc_id in positions:
                    curr_positions = info[1]
                    prev_positions = positions[doc_id]

                    p1 = 0
                    p2 = 0

                    while p1 < len(curr_positions) and p2 < len(prev_positions):
                        difference = curr_positions[p1] - prev_positions[p2]

                        # Range of differences to award points to
                        if difference <= 0:
                            p1 += 1
                        elif difference == 1:
                            positional_score += 1
                            p1 += 1
                            p2 += 1
                        elif difference < 5:
                            positional_score += 0.5
                            p1 += 1
                            p2 += 1
                        elif difference <= 10:
                            positional_score += 0.25
                            p1 += 1
                            p2 += 1
                        elif difference > 10:
                            p2 += 1
                        else:
                            p1 += 1

                positions[doc_id] = info[1]

                if doc_id not in scores:
                    scores[doc_id] = {"tfidf": (info[0] * idf)  * (1 + positional_score)}
                else:
                    scores[doc_id]["tfidf"] += info[0] * idf + positional_score
            
        # Retrieve the top n results as dicts in descending order
        results = dict(heapq.nlargest(number_of_results, scores.items(), key=lambda x: x[1]["tfidf"]))

        # Access disk to retrieve the urls of only the top results
        for doc_id, _ in results.items():
            d_offset = self.doc_finder[doc_id]
            self.doc_index.seek(d_offset)
            # Format: docId | url
            line = self.doc_index.readline()
            results[doc_id]["file"] = line.split("|")[1]

        self.words_index.close()
        self.doc_index.close()

        return results

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