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
from dataclasses import (
    dataclass,
    asdict,
    KW_ONLY
)
from pathlib import Path
import sqlite3
from types import MappingProxyType
from typing import (
    TypeAlias,
    Literal,
    Union,
    Any
)


@dataclass(frozen=True, slots=True)
class Book():
    """
    Represents a book
    """
    title: str
    author: str
    year: int
    KW_ONLY# pylint: disable=pointless-statement
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


_STR_QUERY: TypeAlias = str
_YEAR_QUERY: TypeAlias = Union[int, tuple[int, int]]# mypy doesn't like | here
_CAT_QUERY: TypeAlias = str | Set[str]
_COAUTHOR_QUERY: TypeAlias = _CAT_QUERY

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
        Checks if a book exists

        IN:
            book - the book to find
            full_check - if False, we only check main attributes
                (like title, author, name), if False, we check all

        OUT:
            bool
        """
        ...

    @abstractmethod
    def search_title(self, query: _STR_QUERY) -> Sequence[Book]:
        """
        Searches for books by title using the given query

        IN:
            query - the search query

        OUT:
            sequence of appropriate books
        """
        ...

    @abstractmethod
    def search_author(self, query: _STR_QUERY) -> Sequence[Book]:
        """
        Searches for books by author using the given query

        IN:
            query - the search query

        OUT:
            sequence of appropriate books
        """
        ...

    @abstractmethod
    def search_year(self, query: _YEAR_QUERY) -> Sequence[Book]:
        """
        Searches for books by year using the given query

        IN:
            query - the search query

        OUT:
            sequence of appropriate books
        """
        ...

    @abstractmethod
    def search_category(self, query: _CAT_QUERY) -> Sequence[Book]:
        """
        Searches for books by categories using the given query

        IN:
            query - the search query

        OUT:
            sequence of appropriate books
        """
        ...

    @abstractmethod
    def search_coauthor(self, query: _COAUTHOR_QUERY) -> Sequence[Book]:
        """
        Searches for books by coauthors using the given query

        IN:
            query - the search query

        OUT:
            sequence of appropriate books
        """
        ...
# pylint: enable=unnecessary-ellipsis


_MEMORY_DB = Literal[":memory:"]# pylint: disable=invalid-name

class SQLiteLibraryConnector(AbstractLibraryConnector):
    """
    An implementation of sql library connecter for sqlite
    """
    _TABLE_BOOKS = "books"
    _TABLE_CATS = "categories"
    _TABLE_COAUTHORS = "coauthors"
    _TABLE_J_BOOK_CAT = "j_book_category"
    _TABLE_J_BOOK_COAUTHOR = "j_book_coauthor"

    _INIT_SCRIPT = f"""\
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS {_TABLE_BOOKS} (
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year INT NOT NULL CHECK (year > 0),
    CONSTRAINT pk PRIMARY KEY (title, author, year)
);

CREATE TABLE IF NOT EXISTS {_TABLE_CATS} (
    name TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS {_TABLE_COAUTHORS} (
    name TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS {_TABLE_J_BOOK_CAT} (
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year INT NOT NULL,
    category TEXT NOT NULL,
    FOREIGN KEY (title, author, year)
        REFERENCES {_TABLE_BOOKS} (title, author, year)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (category)
        REFERENCES {_TABLE_CATS} (name)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT pk PRIMARY KEY (title, author, year, category)
);

CREATE TABLE IF NOT EXISTS {_TABLE_J_BOOK_COAUTHOR} (
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year INT NOT NULL,
    coauthor TEXT NOT NULL,
    FOREIGN KEY (title, author, year)
        REFERENCES {_TABLE_BOOKS} (title, author, year)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (coauthor)
        REFERENCES {_TABLE_COAUTHORS} (name)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT pk PRIMARY KEY (title, author, year, coauthor)
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

        self._init_db()

    def __del__(self) -> None:
        self._connection.close()

    def _init_db(self) -> None:
        """
        Inits sqlite + tables
        """
        self._connection.executescript(self._INIT_SCRIPT)
        self._connection.commit()

    def close(self) -> None:
        """
        Closes connection to the db
        """
        self.__del__()

    def _has_table(self, name: str) -> bool:
        query = (
            "SELECT COUNT(1) FROM sqlite_master "
            "WHERE type='table' AND name=(?);"
        )
        cur = self._connection.execute(query, (name,))
        return cur.fetchone()[0] > 0

    def has_book(self, book: Book, full_check: bool = False) -> bool:
        values: tuple[Any, ...]# Somehow mypy finds tuple[object] wtf

        if not full_check:
            stmt = (
                f"SELECT COUNT(1) FROM {self._TABLE_BOOKS} "
                "WHERE title=? AND author=? AND year=?;"
            )
            values = (book.title, book.author, book.year)

        else:
            if book.categories:
                cats = tuple(book.categories)
            else:
                cats = ()
            cats_q_marks = ", ".join("?"*len(cats))

            if book.coauthors:
                coauthors = tuple(book.coauthors)
            else:
                coauthors = ()
            coauthors_q_marks = ", ".join("?"*len(coauthors))

            select = f"SELECT COUNT(1) FROM {self._TABLE_BOOKS} b "
            join_cat = (
                f"JOIN {self._TABLE_J_BOOK_CAT} jc "
                "ON b.title=jc.title AND b.author=jc.author AND b.year=jc.year "
            )
            join_coauthor = (
                f"JOIN {self._TABLE_J_BOOK_COAUTHOR} ja "
                "ON b.title=ja.title AND b.author=ja.author AND b.year=ja.year "
            )
            where = (
                "WHERE b.title=? AND b.author=? AND b.year=? "
            )
            and_cat_in = f"AND jc.category IN ({cats_q_marks}) "
            and_coauthor_in = f"AND ja.coauthor in ({coauthors_q_marks})"
            end = ";"

            stmt = "{}{}{}{}{}{}{}".format(# pylint: disable=consider-using-f-string
                select,
                join_cat if cats else "",
                join_coauthor if coauthors else "",
                where,
                and_cat_in if cats else "",
                and_coauthor_in if coauthors else "",
                end
            )

            values = (book.title, book.author, book.year) + cats + coauthors

        try:
            cur = self._connection.execute(stmt, values)

        except sqlite3.Error as e:# pylint: disable=invalid-name
            self._connection.rollback()
            print(e)
            return False

        total_entries = cur.fetchone()[0]

        # if it's a quick check, we can return earlier
        if not full_check:
            return total_entries > 0

        # we need to use a min values of 1 even if we don't have a cat/co-author
        i = max(len(cats), 1)
        j = max(len(coauthors), 1)

        # we should have cats*coauthors entries
        return total_entries == i*j

    def add_book(self, book: Book) -> bool:
        if self.has_book(book):
            return False

        cur = self._connection.cursor()
        try:
            # Add the book
            ins_book_stmt = (
                f"INSERT INTO {self._TABLE_BOOKS} (title, author, year) "
                "VALUES (?, ?, ?);"
            )
            ins_book_values = (book.title, book.author, book.year)
            cur.execute(ins_book_stmt, ins_book_values)

            if book.categories:
                # Add the categories
                ins_cat_stmt = (
                    f"INSERT INTO {self._TABLE_CATS} (name) VALUES (?) "
                    "ON CONFLICT DO NOTHING;"
                )
                ins_cat_values = ((cat,) for cat in book.categories)
                cur.executemany(ins_cat_stmt, ins_cat_values)

                # Add the cats to the junction table
                ins_j_book_cat_stmt = (
                    (
                        f"INSERT INTO {self._TABLE_J_BOOK_CAT} (title, author, year, category) "
                        "VALUES (?, ?, ?, ?) "
                        "ON CONFLICT DO NOTHING;"
                    )
                )
                ins_j_book_cat_values = (
                    (book.title, book.author, book.year, cat)
                    for cat in book.categories
                )
                cur.executemany(ins_j_book_cat_stmt, ins_j_book_cat_values)

            if book.coauthors:
                # Add the coauthors
                ins_coauthors_stmt = (
                    f"INSERT INTO {self._TABLE_COAUTHORS} (name) VALUES (?) "
                    "ON CONFLICT DO NOTHING;"
                )
                ins_coauthors_values = ((name,) for name in book.coauthors)
                cur.executemany(ins_coauthors_stmt, ins_coauthors_values)

                # Add the coauthors to the junction table
                ins_j_book_coauthor_stmt = (
                    (
                        f"INSERT INTO {self._TABLE_J_BOOK_COAUTHOR} (title, author, year, coauthor) "# pylint: disable=line-too-long
                        "VALUES (?, ?, ?, ?) "
                        "ON CONFLICT DO NOTHING;"
                    )
                )
                ins_j_book_coauthor_values = (
                    (book.title, book.author, book.year, name)
                    for name in book.coauthors
                )
                cur.executemany(ins_j_book_coauthor_stmt, ins_j_book_coauthor_values)

        except sqlite3.Error as e:# pylint: disable=invalid-name
            self._connection.rollback()
            print(e)# TODO: add logging pls
            return False

        # Commit the changes
        self._connection.commit()
        return True

    def remove_book(self, book: Book) -> bool:
        if not self.has_book(book):
            return False

        try:
            # We only need to explicitly delete from the books table
            # j_book_category and j_book_coauthor will be
            # cleared automatically, while the categories and coauthors
            # won't, but we don't care for those extra bits of data
            del_books_stmt = (
                f"DELETE FROM {self._TABLE_BOOKS} "
                "WHERE title=? AND author=? AND year=?;"
            )
            del_books_values = (book.title, book.author, book.year)
            self._connection.execute(del_books_stmt, del_books_values)

        except sqlite3.Error as e:# pylint: disable=invalid-name
            self._connection.rollback()
            print(e)
            return False

        self._connection.commit()
        return True

    def _execute_get_sub_attrs(self, stmt, values) -> frozenset[Any]:
        """
        Method to retrieve sub attributes (like co-authors/categories)

        IN:
            stmt - the sql statement to use
            values - the values for substitution

        OUT:
            frozenset with the book attributes
        """
        try:
            cur = self._connection.execute(stmt, values)

        except sqlite3.Error as e:# pylint: disable=invalid-name
            self._connection.rollback()
            print(e)
            return frozenset()

        return frozenset(data[0] for data in cur.fetchall())

    def _execute_search(self, stmt: str, values: Sequence[Any]) -> Sequence[Book]:
        """
        Method to retrieve books

        IN:
            stmt - the sql statement to use
            values - the values for substitution

        OUT:
            sequence of books
        """
        books: list[Book] = []

        try:
            cur = self._connection.execute(stmt, values)
            for row in cur:
                title = row[0]
                author = row[1]
                year = row[2]

                get_cats_stmt = (
                    f"SELECT category FROM {self._TABLE_J_BOOK_CAT} "
                    "WHERE title=? AND author=? AND year=?;"
                )
                get_coauthors_stmt = (
                    f"SELECT coauthor FROM {self._TABLE_J_BOOK_COAUTHOR} "
                    "WHERE title=? AND author=? AND year=?;"
                )
                values = (title, author, year)

                categories = self._execute_get_sub_attrs(get_cats_stmt, values)
                coauthors = self._execute_get_sub_attrs(get_coauthors_stmt, values)

                books.append(
                    Book(
                        title=title,
                        author=author,
                        year=year,
                        categories=categories,
                        coauthors=coauthors
                    )
                )

        except sqlite3.Error as e:# pylint: disable=invalid-name
            self._connection.rollback()
            print(e)
            return ()

        return tuple(books)

    def search_title(self, query: str) -> Sequence[Book]:
        stmt = f"SELECT * FROM {self._TABLE_BOOKS} WHERE title=?;"
        values = (query,)

        return self._execute_search(stmt, values)

    def search_author(self, query: str) -> Sequence[Book]:
        stmt = f"SELECT * FROM {self._TABLE_BOOKS} WHERE author=?;"
        values = (query,)

        return self._execute_search(stmt, values)

    def search_year(self, query: _YEAR_QUERY) -> Sequence[Book]:
        values: tuple[int] | tuple[int, int]

        if isinstance(query, (tuple, list)):
            stmt = f"SELECT * FROM {self._TABLE_BOOKS} WHERE year BETWEEN ? AND ?;"
            values = (query[0], query[1])

        else:
            stmt = f"SELECT * FROM {self._TABLE_BOOKS} WHERE year=?;"
            values = (query,)

        return self._execute_search(stmt, values)

    def search_category(self, query: _CAT_QUERY) -> Sequence[Book]:
        if isinstance(query, (Set, tuple, list)):
            # Need multiple params since we got multiple cats to check for
            q_marks = ", ".join("?"*len(query))
            # We need DISTINCT since a book can have several categories and we don't need dupes
            stmt = (
                f"SELECT DISTINCT b.title, b.author, b.year FROM {self._TABLE_BOOKS} b "
                f"JOIN {self._TABLE_J_BOOK_CAT} junction "
                "ON b.title=junction.title AND b.author=junction.author AND b.year=junction.year "
                f"WHERE junction.category IN ({q_marks});"
            )
            values = tuple(query)

        else:
            stmt = (
                f"SELECT b.title, b.author, b.year FROM {self._TABLE_BOOKS} b "
                f"JOIN {self._TABLE_J_BOOK_CAT} junction "
                "ON b.title=junction.title AND b.author=junction.author AND b.year=junction.year "
                "WHERE junction.category=?;"
            )
            values = (query,)

        return self._execute_search(stmt, values)

    def search_coauthor(self, query: _COAUTHOR_QUERY) -> Sequence[Book]:
        if isinstance(query, (Set, tuple, list)):
            q_marks = ", ".join("?"*len(query))
            stmt = (
                f"SELECT DISTINCT b.title, b.author, b.year FROM {self._TABLE_BOOKS} b "
                f"JOIN {self._TABLE_J_BOOK_COAUTHOR} junction "
                "ON b.title=junction.title AND b.author=junction.author AND b.year=junction.year "
                f"WHERE junction.coauthor IN ({q_marks});"
            )
            values = tuple(query)

        else:
            stmt = (
                f"SELECT b.title, b.author, b.year FROM {self._TABLE_BOOKS} b "
                f"JOIN {self._TABLE_J_BOOK_COAUTHOR} junction "
                "ON b.title=junction.title AND b.author=junction.author AND b.year=junction.year "
                "WHERE junction.coauthor=?;"
            )
            values = (query,)

        return self._execute_search(stmt, values)










# c = SQLiteLibraryConnector(":memory:")
# b1 = Book(title="Python 101", author="Monika", year=2023, coauthors={"Boop"}, categories={"programming", "python", "language"})
# b2 = Book(title="SQLite for dummies", author="Boop", year=2022, categories={"programming", "sql", "language"})
# b3 = Book(title="Love", author="Monika", year=2024, categories={"romance", "novel"})

# def execute(stmt):
#     print(c._connection.execute(stmt).fetchall())

# def print_tables():
#     print("books:")
#     execute("SELECT * FROM books;")

#     print("coauthors:")
#     execute("SELECT * FROM coauthors;")
#     execute("SELECT * FROM j_book_coauthor;")

#     print("categories:")
#     execute("SELECT * FROM categories;")
#     execute("SELECT * FROM j_book_category;")

# # print("tables:")
# # execute("SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%';")

# # print("Added books")
# c.add_book(b1)
# c.add_book(b2)
# c.add_book(b3)
# # print_tables()

# # print("Removed a book")
# c.remove_book(b1)
# # print_tables()

# # c._connection.set_trace_callback(lambda stmt: print(stmt))
# # execute("SELECT * FROM books WHERE title LIKE 'Love';")


# # print(c.search_author("moni"))
# # print(c.search_author("boop"))
# # print(c.search_title("love"))
# # print(c.search_year(2022))
# # print(c.search_year((2020, 2025)))
# # print(c.search_category("programming"))
# # print(c.search_category("sql"))
# # print(c.search_category("python"))
# # print(c.search_category({"language", "programming"}))
# print(c.has_book(b1, full_check=False))
# print(c.has_book(b2, full_check=False))
# print(c.has_book(b3, full_check=False))
# print(c.has_book(b1, full_check=True))
# print(c.has_book(b2, full_check=True))
# print(c.has_book(b3, full_check=True))
