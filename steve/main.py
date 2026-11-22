from flask import Flask, render_template, request, url_for, redirect
from indexing.search import run_search
import os
import json

app = Flask(__name__)

# Main search page
@app.route('/')
def index():
    return render_template('index.html')

# Retrieve query, run search, and show results page
@app.route('/results')
def results():
    query = request.args.get("q", '')
    results = run_search(query)
    print(results)
    return render_template('results.html', query=query, results=results)

# Return to main page when clicking logo title
@app.route('/home')
def return_to_index():
    return index()

# View actual page from retrieved document
@app.route('/external')
def go_external():
    file = request.args.get("file", '',)
    html_content = ""

    print(file)
    # Find json file that corresponds to the document, get the html content, and display
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        html_content = data["content"]
    
    return html_content 
