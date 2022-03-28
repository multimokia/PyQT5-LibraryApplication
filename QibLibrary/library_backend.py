"""
Module contains library backend implementation

NOTE: this is very hand to maintain.
    If we were to add a new field to the books, we'd have to add a new attribute
    to Book and add a new search method to LibraryConnector.
    This also doesn't support different (generic) book types (but I don't think we need that
    because we use SQL to store data anyway)
"""


from __future__ import annotations

__all__ = ("Book", "SQLiteLibraryConnector")


from abc import (
    ABC,
    abstractmethod
)
from collections.abc import (
    Set,
    Sequence,
    Mapping
)
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
from types import MappingProxyType
from typing import (
    Literal,
    Any
)


@dataclass(frozen=True, kw_only=True, slots=True)
class Book():
    """
    Represents a book
    """
    title: str
    author: str
    year: int
    categories: Set[str] | None = None
    coauthors: Set[str] | None = None

    def to_dict(self) -> MappingProxyType[str, Any]:
        """
        Converts this book into a dict
        """
        return MappingProxyType(asdict(self, dict_factory=dict))

    @classmethod
    def from_dict(cls, dict_: Mapping[str, Any]) -> Book:
        """
        Builds a book from a dict data
        """
        return cls(**dict_)


# pylint: disable=unnecessary-ellipsis
class AbstractLibraryConnector(ABC):
    """
    ABC for sql library connectors
    """
    @abstractmethod
    def add_book(self, book: Book) -> bool:
        """
        Adds a new book to the db

        IN:
            book - a book obj to add

        OUT:
            bool - whether or not the operation was successful
        """
        ...

    @abstractmethod
    def remove_book(self, book: Book) -> bool:
        """
        Removes a book from the db

        IN:
            book - a book obj to remove

        OUT:
            bool - whether or not the operation was successful
        """
        ...

    @abstractmethod
    def has_book(self, book: Book) -> bool:
        """
        Check if this exact book exists in the db

        IN:
            book - a book obj to find

        OUT:
            bool
        """
        ...

    @abstractmethod
    def _search(self, field: str, query: str) -> Sequence[Book]:
        """
        Searches for books using the given field and query

        IN:
            field - the search field
            query - the search query

        OUT:
            sequence of appropriate books
        """
        ...

    def search_title(self, query: str) -> Sequence[Book]:
        """
        Searches for books by title using the given query

        IN:
            query - the search query

        OUT:
            sequence of appropriate books
        """
        return self._search("title", query)

    def search_author(self, query: str) -> Sequence[Book]:
        """
        Searches for books by author using the given query

        IN:
            query - the search query

        OUT:
            sequence of appropriate books
        """
        return self._search("author", query)

    def search_category(self, query: str) -> Sequence[Book]:
        """
        Searches for books by categories using the given query

        IN:
            query - the search query

        OUT:
            sequence of appropriate books
        """
        return self._search("categories", query)
# pylint: enable=unnecessary-ellipsis


_MEMORY_DB = Literal[":memory:"]# pylint: disable=invalid-name

class SQLiteLibraryConnector(AbstractLibraryConnector):
    """
    An implementation of sql library connecter for sqlite
    """
    _CREATE_TABLE_STATEMENT = """\
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS books (
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year INT NOT NULL CHECK (year > 0),
    CONSTRAINT pk PRIMARY KEY (title, author, year)
);

CREATE TABLE IF NOT EXISTS categories (
    name TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS coauthors (
    name TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS j_book_category (
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year INT NOT NULL,
    category TEXT NOT NULL,
    FOREIGN KEY (title, author, year)
        REFERENCES books (title, author, year)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (category)
        REFERENCES categories (name)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT pk PRIMARY KEY (title, year, category)
);

CREATE TABLE IF NOT EXISTS j_book_coauthor (
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year INT NOT NULL,
    coauthor TEXT NOT NULL,
    FOREIGN KEY (title, author, year)
        REFERENCES books (title, author, year)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (coauthor)
        REFERENCES coauthors (name)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT pk PRIMARY KEY (title, year, coauthor)
);\
"""

    def __init__(self, db_path: Path | _MEMORY_DB, **kwargs) -> None:
        """
        Constructor for library connector

        IN:
            db_path - path to the sqlite database
            **kwargs - additional kwargs to use for connection object
        """
        self._db_path = db_path
        self._connection = sqlite3.connect(db_path, **kwargs)

        self._create_tables()

    def _has_table(self, name: str) -> bool:
        query = (
            "SELECT COUNT(*) FROM sqlite_master "
            "WHERE type='table' AND name=(?);"
        )
        cur = self._connection.execute(query, (name,))
        return cur.fetchone()[0] > 0

    def _create_tables(self) -> None:
        self._connection.executescript(self._CREATE_TABLE_STATEMENT)
        self._connection.commit()

    def add_book(self, book: Book) -> bool:
        cur = self._connection.cursor()
        try:
            # Add the book
            ins_book_stmt = "INSERT INTO books (title, author, year) VALUES (?, ?, ?);"
            ins_book_values = (book.title, book.author, book.year)
            cur.execute(ins_book_stmt, ins_book_values)

            if book.categories:
                # Add the categories
                ins_cat_stmt = "INSERT INTO categories (name) VALUES (?);"
                ins_cat_values = ((cat,) for cat in book.categories)
                cur.executemany(ins_cat_stmt, ins_cat_values)

                # Add the cats to the junction table
                ins_j_book_cat_stmt = (
                    "INSERT INTO j_book_category (title, author, year, category) VALUES (?, ?, ?, ?);"
                )
                ins_j_book_cat_values = (
                    (book.title, book.author, book.year, cat)
                    for cat in book.categories
                )
                cur.executemany(ins_j_book_cat_stmt, ins_j_book_cat_values)

            if book.coauthors:
                # Add the coauthors
                ins_coauthors_stmt = "INSERT INTO coauthors (name) VALUES (?);"
                ins_coauthors_values = ((name,) for name in book.coauthors)
                cur.executemany(ins_coauthors_stmt, ins_coauthors_values)

                # Add the coauthors to the junction table
                ins_j_book_coauthor_stmt = (
                    "INSERT INTO j_book_coauthor (title, author, year, coauthor) VALUES (?, ?, ?, ?);"
                )
                ins_j_book_coauthor_values = (
                    (book.title, book.author, book.year, name)
                    for name in book.coauthors
                )
                cur.executemany(ins_j_book_coauthor_stmt, ins_j_book_coauthor_values)

            # Commit the changes
            self._connection.commit()

        except sqlite3.Error as e:# pylint: disable=invalid-name
            print(e)# TODO: add logging pls
            return False

        return True

    def remove_book(self, book: Book) -> bool:
        ...

    def has_book(self, book: Book) -> bool:
        ...

    def _search(self, field: str, query: str) -> Sequence[Book]:
        ...


# c = SQLiteLibraryConnector(":memory:")
# def printer(c, stmt):
#     print(c._connection.execute(stmt).fetchall())
# printer(c, "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%';")
# b = Book(title="Python 101", author="Monika", year=2023, coauthors={"Boop"}, categories={"programming", "science"})
# print(b)
# c.add_book(b)
# printer(c, "SELECT * FROM books;")

# printer(c, "SELECT * FROM coauthors;")
# printer(c, "SELECT * FROM j_book_coauthor;")

# printer(c, "SELECT * FROM categories;")
# printer(c, "SELECT * FROM j_book_category;")
