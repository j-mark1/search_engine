from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def extract(content: str) -> dict:
    stripped = content.lstrip()
    # not html or xml
    if not stripped.startswith("<"):
        return {"title": "", "important": "", "body": content}

    head = stripped[:1000].lower() # might have whitespace in front
    if head.startswith("<?xml") and "<html" not in head:
        soup = BeautifulSoup(content, features="xml")
    else:
        soup = BeautifulSoup(content, "lxml")

    # dont want stuff like js or css stuff
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = soup.title.get_text(" ") if soup.title else ""
    important = " ".join(t.get_text(" ") for t in soup.find_all(["h1", "h2", "h3", "b", "strong", "em"]))
    body = soup.get_text(" ")
    return {"title": title, "important": important, "body": body}