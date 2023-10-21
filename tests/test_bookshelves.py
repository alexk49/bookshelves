"""Tests for all stand alone functions"""
import unittest

from bookshelves import validate_date, confirm_user_input


class TestValidateDate(unittest.TestCase):
    """Tests for validate date function"""

    def test_invalid_date(self):
        invalid_date = validate_date("2023-40-30")
        self.assertFalse(invalid_date)

    def test_wrong_format_date(self):
        wrong_format = validate_date("01-12-2023")
        self.assertFalse(wrong_format)

    def test_correct_date(self):
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
