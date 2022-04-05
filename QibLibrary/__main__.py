from frontend import menu, MenuOption, validatedInput
from library_connectors import SQLiteLibraryConnector, Book
from typing import Callable, Sequence
import os

def main():
    """
    Main function for the QibLibrary.
    """
    CREATE_NEW_DB = False
    if not os.path.isfile("./library.db"):
        print("No library database found. Creating new database...")
        CREATE_NEW_DB = True

    connector = SQLiteLibraryConnector("./library.db")

    if CREATE_NEW_DB:
        connector.add_book(Book("The Great Gatsby", "F. Scott Fitzgerald", 1925, categories=["fiction"]))
        connector.add_book(Book("Ren'Py for Dummies", "Monika", 2017, categories=["programming", "tutorial", "informational"]))
        connector.add_book(Book("Fahrenheit 451", "Ray Bradbury", 1953, categories=["fiction", "science", "dystopia"]))
        connector.add_book(Book("Brave New World", "Aldous Huxley", 1932, categories=["fiction", "dystopia"]))
        connector.add_book(Book("1984", "George Orwell", 1949, categories=["fiction", "dystopia"]))

    while True:
        result: Callable[[SQLiteLibraryConnector|None]] = menu(
            "What would you like to do?",
            MenuOption("Search for books", searchForBooks),
            #MenuOption("Add a book", connector.add_book),
            #MenuOption("Remove a book", connector.remove_book),
            MenuOption("Quit", None)
        )

        if result is None:
            break

        result(connector)
    return
def searchForBooks(conn: SQLiteLibraryConnector):
    """
    Menu flow to search for books in the library

    IN:
        conn: SQLiteLibraryConnector object to perform search queries on
    """
    result: tuple[str, Callable[[str, Sequence[Book]]]] = menu(
        "What would you like to search by?",
        MenuOption("Title", ("title", conn.search_title)),
        MenuOption("Author", ("author", conn.search_author)),
        MenuOption("Year", ("year", conn.search_year)),
        MenuOption("Category", ("category", conn.search_category))
    )

    search_for = validatedInput(f"Which {result[0]} would you like to search for?\n\n>  ", ".+")
    books: Sequence[Book] = result[1](search_for)

    if len(books) == 0:
        print("No books found.")

    #TODO: Put this into a table selector. The results can be selected and put into a "purchase" menu.
    #From there, if the user wants to purchase the book, it can be added to the cart.
    #After returning from the menu, the user is taken back to the search table with the same options.
    for book in books:
        print(book)

    input()

if __name__ == "__main__":
    main()
