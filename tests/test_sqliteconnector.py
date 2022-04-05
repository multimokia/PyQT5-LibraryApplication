"""
Module with testcases for SQLiteLibraryConnector
"""
# pylint: disable=missing-function-docstring
from unittest import TestCase

# pylint: disable-next=import-error # There's no error if we run the tests from the root dir
from QibLibrary.library_connectors import (
    SQLiteLibraryConnector,
    Book
)


class SQLiteConnectorTest(TestCase):
    """
    Test case for SQLiteLibraryConnector
    NOTE: test are done on in-memory db, disk db are not being unittested
        as that would be an integration test
    """
    def setUp(self):
        self.connector = SQLiteLibraryConnector(":memory:")
        # please, don't change these, the tests rely on them
        self.books = (
            Book("Python 101", "Guido van Rossum", 2046, categories={"python", "programming", "science", "education"}),
            Book("1984", "George Orwell", 1949, categories={"dystopian", "political fiction", "social science fiction"}),
            Book(
                title="JS for business",
                author="A not very smart person",
                year=1995,
                categories={"javascript", "js", "not programming", "pain"},
                coauthors={"A person who likes pain", "A person who wants other people to suffer"}
            ),
            Book("How to Ren'Py", "Bob who keeps it simple", 2019),
            Book("Piano for dummies", "Monika", 2026, categories={"education", "piano", "music"}),
            Book("Being a qeeb", "multi", 2031, categories={"horror", "social"})
        )

    def tearDown(self):
        self.connector.close()
        del self.connector

    def _add_books(self):
        # pylint: disable=invalid-name
        for b in self.books:
            self.connector.add_book(b)
        # pylint: enable=invalid-name

    def test_has_table(self):
        # pylint: disable=protected-access
        table_names = (
            self.connector._TABLE_BOOKS,
            self.connector._TABLE_CATS,
            self.connector._TABLE_COAUTHORS,
            self.connector._TABLE_J_BOOK_CAT,
            self.connector._TABLE_J_BOOK_COAUTHOR
        )
        for tbn in table_names:
            with self.subTest(f"Check table exist: {tbn}"):
                self.assertTrue(self.connector._has_table(tbn))

        with self.subTest("Check table doesn't exist"):
            self.assertFalse(self.connector._has_table("faketablename"))
            real_table = self.connector._TABLE_BOOKS
            self.connector._connection.execute(f"DROP TABLE {real_table}")
            self.assertFalse(self.connector._has_table(real_table))
        # pylint: enable=protected-access

    def test_has_book(self):
        # pylint: disable=invalid-name
        for b in self.books:
            with self.subTest("Check has NO books"):
                self.assertFalse(self.connector.has_book(b, full_check=False))
                self.assertFalse(self.connector.has_book(b, full_check=True))

        self.connector.add_book(self.books[0])
        with self.subTest("Check has the added book"):
            self.assertTrue(self.connector.has_book(self.books[0], full_check=False))
            self.assertTrue(self.connector.has_book(self.books[0], full_check=True))
        for b in self.books[1:]:
            with self.subTest(f"Check still has NO other books: {b}"):
                self.assertFalse(self.connector.has_book(b, full_check=False))
                self.assertFalse(self.connector.has_book(b, full_check=True))

        js_book = self.books[2]
        js_book_data = dict(js_book.to_dict())
        js_book_data["coauthors"] = {"Jake"}
        test_book = Book.from_dict(js_book_data)
        self.connector.add_book(test_book)

        # if we skip checking cats/co-authors, we will find the book
        with self.subTest("Check has missing book QUICK check"):
            self.assertTrue(self.connector.has_book(js_book, full_check=False))
        # but full check must fail since the test book has different coauthors
        with self.subTest("Check has NO missing book FULL check"):
            self.assertFalse(self.connector.has_book(js_book, full_check=True))
        # The test book does exist tho
        with self.subTest("Check has the added test book"):
            self.assertTrue(self.connector.has_book(test_book, full_check=False))
            self.assertTrue(self.connector.has_book(test_book, full_check=True))

        book_idx_to_add = (1, 3, 5)
        for id_ in book_idx_to_add:
            self.connector.add_book(self.books[id_])

        for id_ in book_idx_to_add:
            b = self.books[id_]
            with self.subTest(f"Check has all added books: {b}"):
                self.assertTrue(self.connector.has_book(b, full_check=False))
                self.assertTrue(self.connector.has_book(b, full_check=True))

        not_added_book = self.books[4]
        with self.subTest(f"Check still has NO missing book: {not_added_book}"):
            self.assertFalse(self.connector.has_book(not_added_book, full_check=False))
            self.assertFalse(self.connector.has_book(not_added_book, full_check=True))
        # pylint: enable=invalid-name

    def test_add_book(self):
        book = self.books[0]

        self.assertTrue(self.connector.add_book(book))
        # can't add twice he same book
        self.assertFalse(self.connector.add_book(book))

        book_data = dict(book.to_dict())
        book_data["year"] -= 1

        new_book = Book.from_dict(book_data)
        # Should pass since this book was released earlier
        self.assertTrue(self.connector.add_book(new_book))

        self.assertTrue(self.connector.add_book(self.books[3]))
        self.assertTrue(self.connector.add_book(self.books[4]))

    def test_remove_book(self):
        book = self.books[3]

        # it doesn't exist yet
        with self.subTest("Check can't remove non-existing book"):
            self.assertFalse(self.connector.remove_book(book))

        self.connector.add_book(book)
        with self.subTest("Check can remove existing book"):
            self.assertTrue(self.connector.remove_book(book))

        # Should be wiped
        with self.subTest("Check the book has been removed"):
            self.assertFalse(self.connector.has_book(book))
            self.assertFalse(self.connector.has_book(book, full_check=True))

    # NOTE: I use assertFalse/assertTrue for search tests
    # since an empty sequence evalues to False, non-empty to True

    def test_search_title(self):
        self._add_books()

        bad_title = "this should fail"
        with self.subTest(f"Check can't find BAD title: {bad_title}"):
            self.assertFalse(self.connector.search_title(bad_title))

        # pylint: disable=invalid-name
        for b in self.books:
            title = b.title
            with self.subTest(f"Check can find good title: {title}"):
                self.assertTrue(self.connector.search_title(title))
                # case shouldn't matter
                self.assertTrue(self.connector.search_title(title.upper()))
                self.assertTrue(self.connector.search_title(title.lower()))

        # pylint: enable=invalid-name

    def test_search_author(self):
        self._add_books()

        bad_author = "Mr. I don't exist"
        with self.subTest(f"Check can't find BAD author: {bad_author}"):
            self.assertFalse(self.connector.search_author(bad_author))

        # pylint: disable=invalid-name
        for b in self.books:
            author = b.author
            with self.subTest(f"Check can find good author: {author}"):
                self.assertTrue(self.connector.search_author(author))
                # case shouldn't matter
                self.assertTrue(self.connector.search_author(author.upper()))
                self.assertTrue(self.connector.search_author(author.lower()))

        # pylint: enable=invalid-name

    def test_search_year(self):
        self._add_books()

        with self.subTest("Check can't find BAD year"):
            self.assertFalse(self.connector.search_year(1999))
            qeeb = self.books[5].year
            self.assertFalse(self.connector.search_year(qeeb+874))

        # pylint: disable=invalid-name
        for b in self.books:
            year = b.year
            with self.subTest(f"Check can find good year: {year}"):
                self.assertTrue(self.connector.search_year(year))

        good_y_range = (1901, 2095)
        with self.subTest(f"Check can find good years range: {good_y_range}"):
            self.assertTrue(self.connector.search_year(good_y_range))

        bad_y_range = (3457, 3701)
        with self.subTest(f"Check can't find BAD years range: {bad_y_range}"):
            self.assertFalse(self.connector.search_year(bad_y_range))

        # pylint: enable=invalid-name

    def test_search_category(self):
        self._add_books()

        book = self.books[0]
        cats = tuple(book.categories)
        low_cats = tuple(c.lower() for c in cats)
        up_cats = tuple(c.upper() for c in cats)

        for cat in cats:
            with self.subTest(f"Check can find existing cat: {cat}"):
                result = self.connector.search_category(cat)
                self.assertIn(book, result)

        for cat in low_cats + up_cats:
            with self.subTest(f"Check can find modified existing cat: {cat}"):
                result = self.connector.search_category(cat)
                self.assertIn(book, result)

        for cat_set in (cats, low_cats, up_cats):
            with self.subTest(f"Check can find cat set: {cat_set}"):
                result = self.connector.search_category(cat_set)
                self.assertIn(book, result)

    def test_search_coauthor(self):
        self._add_books()

        book = self.books[2]
        coauthors = tuple(book.coauthors)
        low_coauthors = tuple(ca.lower() for ca in coauthors)
        up_coauthors = tuple(ca.upper() for ca in coauthors)

        # pylint: disable=invalid-name

        for ca in coauthors:
            with self.subTest(f"Check can find existing co-author: {ca}"):
                result = self.connector.search_coauthor(ca)
                self.assertIn(book, result)

        for ca in low_coauthors + up_coauthors:
            with self.subTest(f"Check can find modified existing co-author: {ca}"):
                result = self.connector.search_coauthor(ca)
                self.assertIn(book, result)

        for ca_set in (coauthors, low_coauthors, up_coauthors):
            with self.subTest(f"Check can find co-author set: {ca_set}"):
                result = self.connector.search_coauthor(ca_set)
                self.assertIn(book, result)

        # pylint: enable=invalid-name
