# ICSearch
## How to Run ---

Run and create the reversed index by running the following command:
python index.py

Then, run the web GUI search interface with the following command:
flask --app main run --port 5050

Once the page is running, you can run a query on the search engine by entering it in the page's
search bar.

## Files and Folders ---
### index.py

Initializes and calls the creation of the reversed index. If any partial indexes, reversed indexes,
or save files exist from previous runs, it deletes them automatically before recreating new ones.

### main.py

Runs the main Flask application. Handles the page routes and passes info between the reverse index
and the frontend.

### templates/

Folder that contains the HTML file templates of the index page and results page that appear when running
the web interface.

### static/

Folder that contains static content used for the web interface.

### indexing/

Folder that contains all files related to indexing and querying.

### indexing/indexer.py

Main file that does the indexing and query work. Contains the ReverseIndexer class that builds
partial indexes and merges them. Additionally, contains the MemoryUsage class which the ReverseIndexer
class utilizes to adjust the construction of partial indexes to a machine's memory capabilities.

### indexing/parser.py

Contains helper functions to aid tokenization and removal of stopwords

### indexing/search.py

Runs the search with the given query. Restores statistics and file pointer positions of each word
and document back into memory (if not restored already) for efficiency.