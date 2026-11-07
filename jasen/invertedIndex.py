'''
invertedIndex.py

Takes HTML files to build an inverted index.
An inverted index is a map with token as the key
and list of corresponding postings. A posting is 
the representation of the token's occurence in a 
document. 

not allowed to use a database
'''

from pathlib import Path
import json

from posting import Posting
from tokenizer import tokenize
from parser import extract


"""
---------PSEUDO CODE---------
// dont worry about not fitting a single file into mem

partialInvertedIndex = dict()
counter = 0

for each file:
    create a docid
    write (docid, docname) to some idToName file
    data = read(file)
    tokens = tokenize(data)
    for each token:
        add/update posting of the file in that token's entry in the index
    if partialInvertedIndex.size > max size:
        write to a file
    counter++

mergePartialInvIndexes()
"""



class IndexConstructor:
    PARTIAL_FILE_SUFFIX   = "_pii_"
    PARTIAL_FILE_FEXT     = ".pii"
    INVERTED_INDEX_FEXT   = ".inv"
    DOCID_TO_NAME_FEXT    = ".idtn"


    MAX_POSTINGS_COUNT    = 10000

    def __init__(self):
        # map<string, list<posting>> 
        self.partialInvIndex = dict() # maps tokens to lists of postings
        self.partialIndexCount = 0
        self.out_path = ""
        self.out_filename = ""

        self.numPostings = 0
        self.nextId = 0

    def create(self, path: str, out_path: str, out_filename: str):
        """
        Searches recursively in the path for json files
        to construct an inverted index. 

        @param path: path leading to json files
        @param out_path: path to destination file
        @param out_filename: filename of the inverted index file (without file extension)
        """
        self.nextId = 0;
        self.partialInvIndex = dict() # map<str, list<posting>>
        self.partialIndexCount = 0
        self.out_path = out_path
        self.out_filename = out_filename

        paths = self._get_all_paths(path, out_path, out_filename)
        if not paths or len(paths) != 4:
            return
        # path to data, path to output file, inverted index output filepath, inverted index map filepath
        data_path, output_path, out_filepath, out_didToName_path = paths
        self._remove_partialInvIndex_files(out_path)
        print(data_path, output_path, out_filepath, out_didToName_path)
    
        with out_didToName_path.open(mode="w", encoding="utf-8") as didToNameFile:
            abc = 0 # TODO REMOVE ME
            for file in self._yield_all_files(data_path):
                did = self.nextId # doc id
                self.nextId += 1 # dont care about overflow
                
                # format of data = {"url": [], "content": [], "encoding: [] }
                json_data = self._read_json(file)
                if not isinstance(json_data, dict) or "url" not in json_data or "content" not in json_data:
                    print("invalid json data")
                    continue
                url_string = json_data["url"]
                
                if not isinstance(url_string, str) or url_string == "":
                    print("invalid json data")
                    continue
                # write idToName to file
                self.save_idToName(didToNameFile, did, url_string)

                fields = extract(json_data["content"]) # title, important, body
                json_data = None # free up mem by removing a ref to json_data

                # TODO revist this part
                tokens = tokenize(fields["title"]) + tokenize(fields["important"]) + tokenize(fields["body"])
                position = 0
                for token in tokens:
                    # TODO fix this, only works for milestone 1 probably 
                    self.addPostingToIndex(did, token, position)
                    position += 1

                abc += 1
                # if abc >= 10:
                #     print("REMOVE ME")
                #     break

            if self.partialInvIndex:
                self.savePartialInvIndex()


    def addPostingToIndex(self, did: int, token: str, position: int):
        """
        adds a posting to the inverted index
        """
        postings = self.partialInvIndex.setdefault(token, [])
        if postings and postings[-1].did == did:
            postings[-1].positions.append(position)
        else:
            posting = Posting(did)
            posting.positions.append(position)
            postings.append(posting)

        self.numPostings+=1
        if self.numPostings > self.MAX_POSTINGS_COUNT:
            self.savePartialInvIndex()


    def savePartialInvIndex(self):
        filename = (self.out_filename 
                    + self.PARTIAL_FILE_SUFFIX 
                    + str(self.partialIndexCount) 
                    + self.PARTIAL_FILE_FEXT)
        dest = Path(self.out_path) / filename
        self.partialIndexCount+=1

        with open(dest, "w", encoding="utf-8") as file:
            json_dict = dict()
            for token in self.partialInvIndex:
                json_dict[token] = []
                # token - posting
                posting_list = []
                for posting in self.partialInvIndex[token]:
                    posting_dict = {"did": posting.did, "positions": posting.positions}
                    posting_list.append(posting_dict)
                json_dict[token] = posting_list
            json.dump(json_dict, file, indent=2)
        self.numPostings = 0
        self.partialInvIndex = dict()
                



                 

    def save_idToName(self, file, docid: int, docname: str):
        line = str(docid) + ", " + docname + "\n"
        file.write(line)
        return

        



    # ------------------ HELPERS ------------------------

    def _yield_all_files(self, path: Path):
        for item in path.rglob("*.json"):
            if item.is_file():
                yield item

    def _read_json(self, file):
        # Load it into json
        with file.open(mode="r", encoding="utf-8") as json_file:
            # format of data = {"url": [], "content": [], "encoding: [] }
            json_data = json.load(json_file)
        return json_data

    def _err_handle_path(self, data_path: Path, output_path: Path):
        if not data_path.exists():
            err_msg = "data path: " + str(data_path) + " does not exist"
            print(err_msg)
            return False
        if not output_path.exists():
            err_msg = "output path: " + str(output_path) + " does not exist"
            print(err_msg)
            return False
        if not data_path.is_dir():
            err_msg = "data path: " + str(data_path) + " is not directory"
            print(err_msg)
            return False
        if not output_path.is_dir():
            err_msg = "data path: " + str(output_path) + " is not directory"
            print(err_msg)
            return False
        return True

    def _get_all_paths(self, path, out_path, out_filename):
        """Returns data_path, output_path, out_filepath, out_didToName_path"""
        data_path = Path(path)
        output_path = Path(out_path)
        if not self._err_handle_path(data_path, output_path): return ()

        out_filepath = output_path / (out_filename + self.INVERTED_INDEX_FEXT)
        if(out_filepath.exists()):
            print("err output file exists")
            return ()

        out_didToName_path = output_path / (out_filename + self.DOCID_TO_NAME_FEXT)
        out_didToName_path.unlink(missing_ok=True) # remove if exists
        return data_path, output_path, out_filepath, out_didToName_path

    def _remove_partialInvIndex_files(self, out: str):
        outpath = Path(out)
        for file_path in outpath.glob(f"*{self.PARTIAL_FILE_FEXT}"):
            try:
                file_path.unlink()
            except Exception as e:
                pass