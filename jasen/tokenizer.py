"""
tokenizer.py
"""



TABLE = [
        # All control characters are treated as a space (first 32 characters)
        ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 
        ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 
        ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', 
        ' ', ' ', 

        # Treated as empty ("'", '`')
        # Treated all other non alpha num chars as a space such as ('!', '.', '?', '-', ',',  '\x7f' DEL, '"', ':', ';', '_', '~', ect)

        # lower case letters
        ' ', ' ', ' ', ' ', ' ', ' ', ' ', "", ' ', ' ', ' ', ' ', ' ', 
        ' ', ' ', ' ', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ' ', ' ', ' ', 
        ' ', ' ', ' ', ' ', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 
        'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', ' ', ' ', 
        ' ', ' ', ' ', '', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 
        'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', ' ', ' ', 
        ' ', ' ', ' '
]   




def tokenize(text):
    text = text.encode("ascii", "ignore").decode("ascii").translate(TABLE)
    return text.split()
    