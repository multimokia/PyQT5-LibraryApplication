"""
Main module containing the entry point
"""

import os
from typing import Callable, Sequence, TypeAlias, cast
from collections import defaultdict

# pylint: disable=import-error
from .frontend import (
    menu,
    MenuOption,
    validatedInput,
    tableMenu,
    buildTable,
    enterToContinue
)
from .library_connectors import (
    AbstractLibraryConnector,
    SQLiteLibraryConnector,
    Book
)
from .session import Session
from .logs import createLogger
# pylint: enable=import-error


#Create a session object
_SESSION = Session()
_LOGGER = createLogger("QibLibraryMain")

def main():
    """
    Main function for the QibLibrary.
    """
    #Set up the session's vars
    _SESSION.cart: defaultdict[Book, int] = defaultdict(int) # type: ignore
    _LOGGER.info("Creating session...")

    create_new_db = False
    if not os.path.isfile("./library.db"):
        print("No library database found. Creating new database...")
        create_new_db = True

    connector = SQLiteLibraryConnector("./library.db", _LOGGER)

    if create_new_db:
        _LOGGER.info("Existing database not found. Creating a new database.")
        # pylint: disable=line-too-long
        books = (
            Book("The Great Gatsby", "F. Scott Fitzgerald", 1925, categories=["fiction"]),
            Book("Ren'Py for Dummies", "Monika", 2017, categories=["programming", "tutorial", "informational", "renpy"], coauthors=["Michael"]),
            Book("Fahrenheit 451", "Ray Bradbury", 1953, categories=["fiction", "science", "dystopia"]),
            Book("Brave New World", "Aldous Huxley", 1932, categories=["fiction", "dystopia"]),
            Book("1984", "George Orwell", 1949, categories=["fiction", "dystopia"]),
            Book("The Martian", "Andy Weir", 2011, categories=["fiction", "dystopia"]),
            Book("The Lord of the Rings", "J. R. R. Tolkien", 1954, categories=["fiction"]),
            Book("The Hobbit", "J. R. R. Tolkien", 1937, categories=["fiction"]),
            Book("The Catcher in the Rye", "J. D. Salinger", 1951, categories=["fiction"]),
            Book("The Hunger Games", "Suzanne Collins", 2008, categories=["fiction", "dystopia", "battle"]),
            Book("Stacks and Queues", "Michael A. Harrison", 2017, categories=["programming", "tutorial", "informational"]),
            Book("The Art of Computer Programming", "Donald E. Knuth", 1968, categories=["programming", "tutorial", "informational"]),
            Book("The C Programming Language", "Dennis Ritchie", 1972, categories=["programming", "tutorial", "informational", "c"]),
            Book("The Little Prince", "Antoine de Saint-Exupéry", 1943, categories=["fiction"]),
            Book("The Count of Monte Cristo", "Alexandre Dumas", 1844, categories=["fiction"]),
            Book("The Hobbit: An Unexpected Journey", "J. R. R. Tolkien", 1937, categories=["fiction"]),
            Book("The Hobbit: The Desolation of Smaug", "J. R. R. Tolkien", 1937, categories=["fiction"]),
            Book("The Hobbit: The Battle of the Five Armies", "J. R. R. Tolkien", 1937, categories=["fiction"]),
            Book("The Hobbit: The Return of the King", "J. R. R. Tolkien", 1937, categories=["fiction"]),
            Book("The Hobbit: The Silmarillion", "J. R. R. Tolkien", 1937, categories=["fiction"]),
            Book("The Lord of the Rings: The Fellowship of the Ring", "J. R. R. Tolkien", 1954, categories=["fiction"]),
            Book("The Lord of the Rings: The Two Towers", "J. R. R. Tolkien", 1954, categories=["fiction"]),
            Book("Python Programming", "Monika", 2020, categories=["programming", "tutorial", "informational", "python"]),
        )
        for book in books:
            connector.add_book(book)
        del book, books
        # pylint: enable=line-too-long

    try:
        while True:
            result: int|None = menu(
                "What would you like to do?",
                MenuOption("Search for books", 1),
                MenuOption("View cart", 2),
                MenuOption("Checkout", 3),
                MenuOption("Quit", None)
            )

            #User wants to quit
            if result is None:
                break

            if result == 1:
                searchForBooks(connector)

            elif result == 2:
                viewCart()

            elif result == 3:
                checkout()

    except KeyboardInterrupt:
        print("\nExiting...")
        exit(0)

_SearchMenuResult: TypeAlias = tuple[str, Callable[[str], Sequence[Book]]]

def searchForBooks(conn: AbstractLibraryConnector): # pylint: disable=invalid-name
    """
    Menu flow to search for books in the library

    IN:
        conn: SQLiteLibraryConnector object to perform search queries on
    """
    result: _SearchMenuResult = menu(
        "What would you like to search by?",
        MenuOption("Title", ("title", conn.search_title)),
        MenuOption("Author", ("author", conn.search_author)),
        MenuOption("Year", ("year", conn.search_year)),
        MenuOption("Category", ("category", conn.search_category))
    )

    search_for = validatedInput(f"Which {result[0]} would you like to search for?\n\n>  ", ".+")
    books: Sequence[Book] = result[1](search_for)
    books = cast(list[Book], books)

    if len(books) == 0:
        print("No books found.")
        enterToContinue()
        return

    try:
        while True:
            selected_book = tableMenu(
                "Add to cart (ctrl+c to return)",
                buildTable(
                    ["Title", "Author", "Year", "Categories", "Co-authors"],
                    books,
                    amt_padding=2
                ),
                books
            )

            if selected_book is not None:
                add_to_cart: bool = menu(
                    f"Add {selected_book.title} to cart?",
                    MenuOption("Yes", True),
                    MenuOption("No", False)
                )

                if add_to_cart:
                    _SESSION.cart[selected_book] += 1 # type: ignore


    except KeyboardInterrupt:
        print("\nExiting search...")
        enterToContinue()

def viewCart():# pylint: disable=invalid-name
    """
    Menu flow to view the cart

    OUT:
        None
    """
    if not _SESSION.cart:
        print("Cart is empty.")
        enterToContinue()
        return

    try:
        while True:
            selected_book = tableMenu(
                "View cart (select an item to remove it from the cart, ctrl+c to exit)",
                buildTable(
                    ["Title", "Author", "Year", "Categories", "Co-authors"],
                    list(_SESSION.cart.keys()),
                    amt_padding=2
                ),
                list(_SESSION.cart.keys())
            )

            if selected_book is not None:
                should_remove: bool = menu(
                    f"Remove {selected_book.title} from cart?",
                    MenuOption("Yes", True),
                    MenuOption("No", False)
                )

                if should_remove:
                    if _SESSION.cart[selected_book] > 0:
                        _SESSION.cart[selected_book] -= 1

                    if _SESSION.cart[selected_book] == 0:
                        _SESSION.cart.pop(selected_book)

    except KeyboardInterrupt:
        print("\nExiting cart...")
        enterToContinue()


def checkout():
    """
    Menu flow to checkout books from the library
    """
    cart_empty: bool = not _SESSION.cart

    if cart_empty:
        print("Cart is empty.")
        enterToContinue()
        return

    print("Items in cart:")
    for book, amt in _SESSION.cart.items():
        print(f"{amt}x {book.title} by {book.author}")

    enterToContinue()
    checkout_cart: bool = menu(
        "Checkout?",
        MenuOption("Yes", True),
        MenuOption("No", False)
    )

    if checkout_cart:
        _checkout_items = "".join(
            f"{amt}x {book.title} by {book.author}\n"
            for book, amt in _SESSION.cart.items()
        )
        _LOGGER.info(_checkout_items)

        _SESSION.cart.clear()
        print("Successfully checked out. Thank you for your purchase.")
        enterToContinue()

if __name__ == "__main__":
    main()
