"""Tests for bookshelves class"""
import unittest
from os.path import exists, join
from os import remove

from bookshelves import Bookshelves, Book


class TestBookshelvesClass(unittest.TestCase):
    """This is used to test the Bookshelves Class and all its methods."""

    def setUp(self):
        self.path_to_test_db = join("tests", "test.db")
        self.db_headers = list(Book.setDefaultDict().keys())

        test_book_metadata = {
            "id": "1",
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

        self.test_book = Book(test_book_metadata)

    @classmethod
    def tearDownClass(cls):
        """Once run is finished delete test db"""
        remove(join("tests", "test.db"))

    def test_bookshelves_init(self):
        """Tests for bookshelves init"""
        bookshelves = Bookshelves(self.path_to_test_db)
        self.assertTrue(exists(bookshelves.db))
        self.assertEqual(bookshelves.db, self.path_to_test_db)

    def test_new_db_schema(self):
        """Tests newly made db schema"""
        bookshelves = Bookshelves(self.path_to_test_db)
        connection, cursor = bookshelves.getConnection()
        query = cursor.execute("""SELECT name FROM sqlite_master WHERE type='table'""")
        result = query.fetchone()
        print("testing table name is correctly set")
        self.assertEqual((result["name"]), "bookshelves")
        query
        print("testing table headers are correctly set")
        for db_row, expected_header in zip(
            connection.execute("pragma table_info('bookshelves')").fetchall(),
            self.db_headers,
        ):
            self.assertEqual(db_row["name"], expected_header)

    def test_add_book_to_db(self):
        """Testing adding book to database"""
        bookshelves = Bookshelves(self.path_to_test_db)
        connection, cursor = bookshelves.getConnection()

        bookshelves.addToDatabase(self.test_book)

        query = cursor.execute(
            """SELECT isbn_13 FROM bookshelves WHERE isbn_13 = ?""",
            (self.test_book.isbn_13,),
        )
        result = query.fetchone()

        self.assertEqual(result["isbn_13"], self.test_book.isbn_13)

    def test_checkIfIDExists(self):
        """Testing checkIfIDEexists method for book to database"""
        bookshelves = Bookshelves(self.path_to_test_db)
        # test id value will always be 1
        # when created by previous addBook
        test_id = "1"
        check = bookshelves.checkIfIDExists(test_id)
        self.assertTrue(check)

    def test_checkIfIDExists_with_false_value(self):
        """Testing checkIfIdExists method with false id value"""
        bookshelves = Bookshelves(self.path_to_test_db)
        test_id = "800000"
        check = bookshelves.checkIfIDExists(test_id)
        self.assertFalse(check)

    def test_updateValues(self):
        """Testing updating values works"""
        bookshelves = Bookshelves(self.path_to_test_db)
        self.test_book.comments = "great book"
        bookshelves.updateValues(self.test_book)

        connection, cursor = bookshelves.getConnection()

        query = cursor.execute(
            """SELECT comments FROM bookshelves WHERE id = ?""",
            (self.test_book.id,),
        )
        result = query.fetchone()

        self.assertEqual(result["comments"], self.test_book.comments)


if __name__ == "__main__":
    unittest.main(verbosity=2)
