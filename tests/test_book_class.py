"""Tests for book class methods"""
import unittest
from unittest import mock
from datetime import datetime

from bookshelves import Book


class TestBookClass(unittest.TestCase):
    """This is used to test the Book Class and all its methods.
    The isbn used for testing is:
    9780747579885 - Jonathan Strange and Mr Norrel
    """

    def setUp(self):
        """
        The test_book_metadata is the info fetched from the open library via:

        Book.openLibIsbnSearch(9780747579885)

        This is used so tests can be carried out offline.
        """
        self.test_book_metadata = {
            "title": "Jonathan Strange and Mr. Norrell",
            "primary_author_key": "/authors/OL1387961A",
            "primary_author": "Susanna Clarke",
            "secondary_authors_keys": "",
            "secondary_authors": "",
            "isbn_13": "9780747579885",
            "edition_publish_date": "September 5, 2005",
            "number_of_pages": 1024,
            "publisher": "Bloomsbury Publishing PLC",
            "open_lib_key": "/books/OL7962789M",
            "goodreads_identifier": "823763",
            "librarything_identifier": "1060",
        }

    def test_book_init(self):
        """Test init Book class"""
        datestamp = datetime.today().strftime("%Y-%m-%d")

        book = Book(self.test_book_metadata)
        self.assertEqual(book.title, self.test_book_metadata["title"])
        self.assertEqual(
            book.primary_author_key, self.test_book_metadata["primary_author_key"]
        )
        self.assertEqual(book.primary_author, self.test_book_metadata["primary_author"])
        self.assertEqual(
            book.secondary_authors_keys,
            self.test_book_metadata["secondary_authors_keys"],
        )
        self.assertEqual(
            book.secondary_authors, self.test_book_metadata["secondary_authors"]
        )
        self.assertEqual(book.isbn_13, self.test_book_metadata["isbn_13"])
        self.assertEqual(
            book.edition_publish_date, self.test_book_metadata["edition_publish_date"]
        )
        self.assertEqual(
            book.number_of_pages, self.test_book_metadata["number_of_pages"]
        )
        self.assertEqual(book.publisher, self.test_book_metadata["publisher"])
        self.assertEqual(book.open_lib_key, self.test_book_metadata["open_lib_key"])
        self.assertEqual(
            book.goodreads_identifier, self.test_book_metadata["goodreads_identifier"]
        )
        self.assertEqual(
            book.librarything_identifier,
            self.test_book_metadata["librarything_identifier"],
        )
        self.assertEqual(book.date_added, datestamp)
        self.assertEqual(book.date_finished, datestamp)
        self.assertEqual(book.comments, "")

    def test_default_dict(self):
        default_dict = Book.setDefaultDict()
        self.assertEqual("", default_dict["id"])
        self.assertEqual("", default_dict["comments"])

        datestamp = datetime.today().strftime("%Y-%m-%d")

        self.assertEqual(datestamp, default_dict["date_added"])

    def test_valid_isbn(self):
        valid_isbn = "9780747579885"
        self.assertTrue(Book.validateISBN(valid_isbn))

    def test_invalid_isbn(self):
        self.assertFalse(Book.validateISBN("jafgl"))

    def test_isbn_10(self):
        self.assertFalse(Book.validateISBN("0747579881"))

    @mock.patch("bookshelves.input", create=True)
    def test_AddComments(self, mocked_input):
        """Testing adding comments to book object"""
        book = Book(self.test_book_metadata)
        mocked_input.side_effect = ["test comment"]
        book.addComments()
        self.assertEqual(book.comments, "test comment")


if __name__ == "__main__":
    unittest.main(verbosity=2)
