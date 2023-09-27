"""Rosewater is a command line app for keeping track of the books"""
import argparse
import csv
from datetime import datetime
import logging
import os
import sqlite3
import sys
from typing import Type, List, Dict

import requests

logging.basicConfig(
    level=logging.DEBUG, format=" %(asctime)s -  %(levelname)s -  %(message)s"
)

DATA_FOLDER = "data"

PATH_TO_DATABASE = os.path.join(DATA_FOLDER, "bookshelf.db")
PATH_TO_CSV = os.path.join(DATA_FOLDER, "bookshelf.csv")

parser = argparse.ArgumentParser()

parser.add_argument("-a", "--add", help="Add to database")
parser.add_argument(
    "-e", "--export", action="store_true", help="Export database to csv"
)
parser.add_argument("-i", "--import_csv", help="Import csv file to database")


class Book:
    """Class for individual book entries"""

    def __init__(self, book_metadata: Dict[str, str]):
        """Create new book object from book metadata"""
        try:
            # keys from csv import
            self.title = book_metadata["title"]
            self.author = book_metadata["author"]
            self.isbn = book_metadata["isbn"]
            self.num_of_pages = book_metadata["number-of-pages"]
            self.pub_date = book_metadata["publication-date"]
            self.publisher = book_metadata["publisher"]
            self.open_lib_work_key = book_metadata["open-lib-key"]

        except KeyError:
            # keys from open lib import
            self.title = book_metadata["title"]
            self.author = book_metadata["author"]
            self.isbn = book_metadata["isbn"]
            self.num_of_pages = book_metadata["num_of_pages"]
            self.pub_date = book_metadata["pub_date"]
            self.publisher = book_metadata["publisher"]
            self.open_lib_work_key = book_metadata["work_key"]

    def __repr__(self):
        """Return a string of the expression that creates the object"""
        return f"{self.__class__.qualname__}"

    def __str__(self):
        """Return human readable string"""
        return f"{self.title} by {self.author}, published in {self.pub_date} by {self.publisher}"

    def __iter__(self):
        """Create iterable of book metadata."""
        return iter(
            [
                self.title,
                self.author,
                self.isbn,
                self.num_of_pages,
                self.pub_date,
                self.publisher,
                self.open_lib_work_key,
            ]
        )

    def writeToCSV(self):
        """Write object book to csv."""
        output_filename = self.isbn + ".csv"
        output_filepath = os.path.join(DATA_FOLDER, output_filename)
        with open(output_filepath, "w") as output:
            writer = csv.writer(output)
            writer.writerow(
                [
                    "title",
                    "author",
                    "isbn",
                    "number-of-pages",
                    "publication-date",
                    "publisher",
                    "open-lib-key",
                ]
            )
            writer.writerow(self)


class Bookshelves:
    """Class for database of books"""

    def __init__(self, path_to_database: str) -> None:
        """Create new bookshelves database object"""
        if os.path.exists(path_to_database):
            database = path_to_database
        else:
            database = self.createNewDatabase(path_to_database)
        self.db = database

    @classmethod
    def createNewDatabase(cls, path_to_database: str) -> str:
        """Create new database file with standard rows."""
        connection = sqlite3.connect(path_to_database)
        cursor = connection.cursor()
        cursor.execute(
            "CREATE TABLE bookshelf(title, author, isbn, num_of_pages, pub_date, publisher, open_lib_work_key)"
        )
        connection.close()
        return path_to_database

    def getConnection(self):
        """In order to execute commands you have to create a connection
        and then a database cursor"""
        connection = sqlite3.connect(self.db)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        return connection, cursor

    def closeDB(self, connection: Type[sqlite3.Connection]):
        """Close existing database connection."""
        connection.close()

    def addToDatabase(self, book: Book):
        """Add a book to the database."""
        logging.info("Inserting %s into %s", book.title, PATH_TO_DATABASE)
        connection, cursor = self.getConnection()
        cursor.execute(
            """INSERT into "bookshelf" (title, author, isbn, num_of_pages, pub_date, publisher, open_lib_work_key) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                book.title,
                book.author,
                book.isbn,
                book.num_of_pages,
                book.pub_date,
                book.publisher,
                book.open_lib_work_key,
            ),
        )
        connection.commit()
        self.closeDB(connection)

    def exportToCSV(self, PATH_TO_CSV: str):
        """Export database to csv file."""
        connection, cursor = self.getConnection()
        bookshelf = cursor.execute("""SELECT * from bookshelf""")

        logging.debug(bookshelf)
        logging.debug(type(bookshelf))

        datestamp = datetime.today().strftime("%Y%m%d")

        output_filename = "bookshelf-" + datestamp + ".csv"
        output_filepath = os.path.join(DATA_FOLDER, output_filename)

        with open(output_filepath, "w") as output:
            writer = csv.writer(output)
            writer.writerow(
                [
                    "title",
                    "author",
                    "isbn",
                    "number-of-pages",
                    "publication-date",
                    "publisher",
                    "open-lib-key",
                ]
            )
            for book in bookshelf:
                writer.writerow(book)

        self.closeDB(connection)

    def importFromCSV(self, import_csv_file: str):
        """Import a csv file to bookshelves database."""
        print(
            """If your CSV has the following columns in order,
then it will be directly imported into the database:
title,
author,
isbn,
number-of-pages,
publication-date,
publisher,
open-lib-key

Otherwise, it must include the isbn for each title and the book metadata will be fetched from the open library.
"""
        )

        check = input("Would you like to continue? y/n: ")

        if confirm_user_input(check):
            bookshelves = Bookshelves(PATH_TO_DATABASE)

            columns_list = [
                "title",
                "author",
                "isbn",
                "number-of-pages",
                "publication-date",
                "publisher",
                "open-lib-key",
            ]

            with open(import_csv_file, "r") as csv_file:
                reader = csv.DictReader(csv_file)

                logging.debug("Headings: %s ", reader.fieldnames)
                headings = reader.fieldnames
                print(type(headings))

                if reader.fieldnames == columns_list:
                    logging.info("Importing data directly from csv file")

                    books_metadata = list(reader)

                    logging.debug(books_metadata)
                    logging.debug(books_metadata[0]["title"])

                    for book_metadata in books_metadata:
                        book = Book(book_metadata)

                        logging.debug(type(book))

                        bookshelves.addToDatabase(book)

                else:
                    logging.info("Getting data from open library")

                    for row in reader:
                        isbn = row["isbn"]
                        logging.debug(isbn)
                        logging.debug(type(isbn))

                        results = open_lib_search(isbn)

                        book_metadata = results[0]
                        logging.debug(book_metadata)

                        book = Book(book_metadata)
                        logging.debug(book)

                        bookshelves.addToDatabase(book)


def open_lib_search(isbn: str) -> List[Dict[str, str]]:
    """Get book data using general open library search api."""
    url = "https://openlibrary.org/search.json"

    # create url query
    search_url = url + "?q=" + isbn + "&limit=20"

    response = requests.get(search_url)
    response_dict = response.json()

    results = []
    num = 0
    # get basic biblographic data
    try:
        work_key = response_dict["docs"][num]["key"]
        title = response_dict["docs"][num]["title"]
        author = response_dict["docs"][num]["author_name"]
        # handle multiple authors
        if len(author) == 1:
            author = author[0]
        else:
            author = ", ".join(author)

        # handle values that caused key errors on rarer books in testing

        num_of_pages = response_dict["docs"][num]["number_of_pages_median"]
        first_publish_date = response_dict["docs"][num]["first_publish_year"]
        publisher = response_dict["docs"][num]["publisher"][0]

    except KeyError as e:
        # if work doesn't have basic biblographic data ignore it
        logging.info(f"{e}: invalid book")

    results.append(
        {
            "work_key": work_key,
            "title": title,
            "pub_date": first_publish_date,
            "num_of_pages": num_of_pages,
            "author": author,
            "isbn": isbn,
            "publisher": publisher,
        }
    )

    return results


def validate_isbn(isbn: str) -> bool:
    """Test for valid isbn"""
    logging.debug(isbn)
    logging.debug(type(isbn))

    isbn = isbn.strip()
    if isbn.isdigit() is False:
        logging.info("ISBN contains characters that aren't numbers")
        return False
    else:
        length = len(isbn)
        if length == 10 or length == 13:
            return True
        else:
            logging.info("ISBN is invalid length")
            logging.debug(len(isbn))
            return False


def confirm_user_input(check: str):
    """Used to check user input for yes or no."""
    if check[0].lower() == "y":
        return True
    else:
        logging.critical("Exiting program.")
        sys.exit(1)


def usage():
    logging.info(
        """
Usage:
    rosewater.py [args] [opt-book-isbn]
    # Add book to datebase:
    rosewater.py -a [valid-isbn]
    """
    )


def main():
    logging.debug(sys.argv)
    if (len(sys.argv)) == 1:
        logging.info("Invalid usage: no args passed\n")
        usage()
        sys.exit(1)
    else:
        args = parser.parse_args()
        logging.debug(args)
        if args.add:
            isbn = args.add

            if not validate_isbn(isbn):
                logging.critical("Invalid isbn given.")
                sys.exit(1)

            logging.info("searching for %s", isbn)
            books_metadata = open_lib_search(isbn)

            if not books_metadata:
                logging.critical("No results found for %s", isbn)

            logging.debug(books_metadata)

            book = Book(books_metadata[0])

            logging.info(book)

            check = input(
                f"Is {book} the book you want to add to your bookshelf? y/n: "
            )
            check = confirm_user_input(check)

            if check:
                logging.info("Writing %s to csv", book.isbn)
                book.writeToCSV()

                logging.info("Establishing Bookshelf class")
                bookshelf = Bookshelves(PATH_TO_DATABASE)

                logging.info("Writing %s to bookshelf", book.isbn)
                bookshelf.addToDatabase(book)
        elif args.export:
            logging.info("Establishing Bookshelf class")
            bookshelf = Bookshelves(PATH_TO_DATABASE)

            bookshelf.exportToCSV(PATH_TO_CSV)
        elif args.import_csv:
            logging.debug(args.import_csv)
            import_csv_filepath = args.import_csv
            if os.path.exists(import_csv_filepath) is False:
                logging.critical("CSV filepath does not exist: %s", import_csv_filepath)

            bookshelves = Bookshelves(PATH_TO_DATABASE)

            bookshelves.importFromCSV(import_csv_filepath)

        else:
            logging.info("Something else")


if __name__ == "__main__":
    main()
