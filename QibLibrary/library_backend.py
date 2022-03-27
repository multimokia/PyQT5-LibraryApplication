"""
Module contains library backend implementation

NOTE: this is very hand to maintain.
    If we were to add a new field to the books, we'd have to add a new attribute
    to Book and add a new search method to LibraryConnector.
    This also doesn't support different (generic) book types (but I don't think we need that
    because we use SQL to store data anyway)
"""


from __future__ import annotations

__all__ = ("Book", "LibraryConnector")


from dataclasses import dataclass
from collections.abc import (
    Set,
    Sequence,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class Book():
    """
    Represents a book
    """
    title: str
    authors: Set[str]
    categories: Set[str]


class LibraryConnector():
    """
    A connecter to sql database
    """
    def __init__(self, db_connection) -> None:
        """
        Constructor for library connector

        IN:
            db_connection - connection object for the sql database
        """
        self.db_connection = db_connection

    def add_book(self, book: Book) -> bool:
        """
        Adds a new book to the db

        IN:
            book - a book obj to add

        OUT:
            bool - whether or not the operation was successful
        """
        ...

    def remove_book(self, book: Book) -> bool:
        """
        Removes a book from the db

        IN:
            book - a book obj to remove

        OUT:
            bool - whether or not the operation was successful
        """
        ...

    def has_book(self, book: Book) -> bool:
        """
        Check if this exact book exists in the db

        IN:
            book - a book obj to find

        OUT:
            bool
        """
        ...

    def _search(self, field: str, query: str) -> Sequence[Book]:
        ...

    def search_title(self, query: str) -> Sequence[Book]:
        """
        Searches for books by titles using the given query

        IN:
            query - the search query

        OUT:
            sequence of appropriate books
        """
        return self._search("title", query)

    def search_author(self, query: str) -> Sequence[Book]:
        """
        Searches for books by authors using the given query

        IN:
            query - the search query

        OUT:
            sequence of appropriate books
        """
        return self._search("authors", query)

    def search_category(self, query: str) -> Sequence[Book]:
        """
        Searches for books by categories using the given query

        IN:
            query - the search query

        OUT:
            sequence of appropriate books
        """
        return self._search("categories", query)
