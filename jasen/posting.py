"""
posting.py
"""

class Posting():
    def __init__(self, did: int):
        self.did = did # document id
        self.positions = []
        # tf stuff later here
        self.title_tf = 0
        self.important_tf = 0

    @property
    def tf(self):
        return len(self.positions)

    def serialize(self):
        pass