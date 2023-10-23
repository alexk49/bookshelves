"""Tests for bookshelves class"""
import csv
import unittest
from unittest import mock
from os.path import exists, join
from os import remove

from bookshelves import Bookshelves, Book


class TestBookshelvesClass(unittest.TestCase):
    """This is used to test the Bookshelves Class and all its methods."""

    def setUp(self):
        self.path_to_test_db = join("tests", "test.db")
        self.db_headers = list(Book.setDefaultDict().keys())

        self.test_book_metadata = {
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
            "date_added": "2023-10-23",
            "date_finished": "2023-10-23",
            "comments": "",
        }

        self.test_book = Book(self.test_book_metadata)

    @classmethod
    def tearDownClass(cls):
        """Once run is finished delete test db"""
        remove(join("tests", "test.db"))
        remove(join("tests", "test-import.csv"))
        remove(join("tests", "test-export.csv"))

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

    def test_exportToCSV(self):
        path_to_csv = join("tests", "test-export.csv")
        bookshelves = Bookshelves(self.path_to_test_db)

        connection, cursor = bookshelves.getConnection()

        print("writing to csv")
        bookshelves.exportToCSV(path_to_csv)

        print("testing csv exists")
        self.assertTrue(exists(path_to_csv))

        with open(path_to_csv, "r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)

            print("checking headers match expected schema")
            self.assertEqual(self.db_headers, reader.fieldnames)

            target_row = 1

            for num, row in enumerate(reader):
                if num == target_row:
                    self.assertEqual(row["id"], self.test_book.id)
                    self.assertEqual(row["title"], self.test_book.title)
                    break

    @mock.patch("bookshelves.input", create=True)
    def test_importFromCSV(self, mocked_input):
        test_book2_metadata = {
            "id": "",
            "title": "Lolly Willowes",
            "primary_author_key": "/authors/OL39232A",
            "primary_author": "Sylvia Townsend Warner",
            "secondary_authors_keys": ", /authors/OL20510A",
            "secondary_authors": ", Sylvia Townsend Warner",
            "isbn_13": "9781844088058",
            "edition_publish_date": "2012",
            "number_of_pages": 224,
            "publisher": "Little, Brown Book Group Limited",
            "open_lib_key": "/books/OL28472551M",
            "goodreads_identifier": "",
            "librarything_identifier": "",
            "date_added": "2023-10-23",
            "date_finished": "2023-10-23",
            "comments": "",
        }

        updated_comments = "NEW UPDATED COMMENT"

        self.test_book_metadata["comments"] = updated_comments

        output_filepath = join("tests", "test-import.csv")

        with open(output_filepath, "w") as file:
            writer = csv.DictWriter(file, self.test_book_metadata.keys())
            writer.writeheader()
            writer.writerow(self.test_book_metadata)
            writer.writerow(test_book2_metadata)

        self.assertTrue(exists(output_filepath))

        bookshelves = Bookshelves(self.path_to_test_db)

        mocked_input.side_effect = ["y"]
        bookshelves.importFromCSV(output_filepath)

        connection, cursor = bookshelves.getConnection()

        query = cursor.execute("""SELECT * FROM bookshelves""")

        result = query.fetchall()

        for num, row in enumerate(result):
            if num == 0:
                self.assertEqual(str(row["id"]), self.test_book_metadata["id"])
                self.assertEqual(row["comments"], updated_comments)
            elif num == 1:
                self.assertEqual(row["title"], test_book2_metadata["title"])
                self.assertEqual(
                    row["primary_author"], test_book2_metadata["primary_author"]
                )
                self.assertEqual(row["isbn_13"], test_book2_metadata["isbn_13"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
