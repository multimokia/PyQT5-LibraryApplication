"""
Module with testcases for Book
"""
# pylint: disable=missing-function-docstring
from unittest import TestCase

# pylint: disable-next=import-error
from QibLibrary.library_connectors import Book


class BookTest(TestCase):
    """
    Test case for Book
    """
    def test_eq(self):
        book1 = Book("How to live with pain", "A RenPy user", 2022, categories={"medicine", "psychology"}, coauthors={"MAS devs"})

        self.assertEqual(book1, Book("How to live with pain", "A RenPy user", 2022, categories={"medicine", "psychology"}, coauthors={"MAS devs"}))
        self.assertNotEqual(book1, Book("How to live with pain", "A RenPy user", 2022))
        self.assertNotEqual(book1, Book("How to live with pain", "A RenPy user", 2021, categories={"medicine", "psychology"}, coauthors={"MAS devs"}))
        self.assertNotEqual(book1, Book("How to live with pain", "A RenPy user", 2022, categories={"horror", "medicine", "psychology"}, coauthors={"MAS devs"}))
        self.assertNotEqual(book1, Book("How to live with pain", "A RenPy user", 2022, categories={"medicine", "psychology"}, coauthors={"devs"}))
        self.assertNotEqual(book1, Book("How to live with everyday pain", "A RenPy user", 2022, categories={"medicine", "psychology"}, coauthors={"MAS devs"}))

    def test_to_dict(self):
        book = Book("title str", "author str", 9999, categories={"cat1", "cat2"}, coauthors={"coauthor1"})
        data = book.to_dict()

        with self.subTest("Check keys"):
            self.assertEqual(tuple(data.keys()), book.__slots__)

        for attr in book.__slots__:
            with self.subTest(f"Check value for: '{attr}'"):
                self.assertEqual(data[attr], getattr(book, attr))

    def test_from_dict(self):
        data = dict(title="title str", author="author str", year=(2001, 2005), categories={"cat1", "cat2"}, coauthors={"co-author1"})
        book = Book.from_dict(data)

        for attr in book.__slots__:
            with self.subTest(f"Check atrr value for: '{attr}'"):
                self.assertEqual(getattr(book, attr), data[attr])
