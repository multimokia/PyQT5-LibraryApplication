from library_connectors import Book

class Session:
    def __init__(self):
        self.cart: list[Book] = []
