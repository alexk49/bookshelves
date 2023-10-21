import unittest
from datetime import datetime

from bookshelves import Book, Bookshelves, validate_date, confirm_user_input

# Book, Bookshelves, validate_date, confirm_user_input


class TestValidateDate(unittest.TestCase):
    """Tests for validate date function"""

    def test_invalid_date(self):
        invalid_date = validate_date("2023-40-30")
        self.assertFalse(invalid_date)

    def test_wrong_format_date(self):
        wrong_format = validate_date("01-12-2023")
        self.assertFalse(wrong_format)

    def correct_date(self):
        valid_date = validate_date("2023-12-25")
        self.assertTrue(valid_date)


class TestConfirmUserInput(unittest.TestCase):
    """Tests for confirm user input function"""

    def test_correct_input(self):
        correct_input = confirm_user_input("yes")
        self.assertTrue(correct_input)

    def test_correct_input_upper_case(self):
        upper_case_input = confirm_user_input("YES")
        self.assertTrue(upper_case_input)

    def test_no_input(self):
        """input other than yes should raise sys.exit(1)"""
        with self.assertRaises(SystemExit) as command:
            confirm_user_input("No")

        # check exit code
        self.assertEqual(command.exception.code, 1)

    def test_random_input(self):
        """input other than yes should raise sys.exit(1)"""
        with self.assertRaises(SystemExit) as command:
            confirm_user_input("jgafjgda")

        # check exit code
        self.assertEqual(command.exception.code, 1)


class TestDefaultDict(unittest.TestCase):
    """Tests for the Book class object.
    Static methods are tested first."""

    def test_default_dict(self):
        default_dict = Book.setDefaultDict()
        self.assertEqual("", default_dict["id"])
        self.assertEqual("", default_dict["comments"])

        datestamp = datetime.today().strftime("%Y-%m-%d")

        self.assertEqual(datestamp, default_dict["date_added"])


class TestValidateISBNs(unittest.TestCase):
    """The isbn used for testing is:
    9780747579885 - Jonathan Strange and Mr Norrel
    """

    def test_valid_isbn(self):
        valid_isbn = "9780747579885"
        self.assertTrue(Book.validateISBN(valid_isbn))

    def test_invalid_isbn(self):
        self.assertFalse(Book.validateISBN("jafgl"))

    def test_isbn_10(self):
        self.assertFalse(Book.validateISBN("0747579881"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
