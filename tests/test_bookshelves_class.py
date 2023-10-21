import unittest
from os.path import exists, join, remove

from bookshelves import Bookshelves


class TestBookshelvesClass(unittest.TestCase):
    """This is used to test the Bookshelves Class and all its methods."""

    def setUp(self):
        self.path_to_test_db = join("tests", "test.db")

    def tearDown(self):
        remove(self.path_to_test_db)

    def test_book_shelves_init(self):
        bookshelves = Bookshelves(self.path_to_test_db)
        self.assertTrue(exists(bookshelves.db))
        self.assertEqual(bookshelves.db, self.path_to_test_db)


if __name__ == "__main__":
    unittest.main(verbosity=2)
