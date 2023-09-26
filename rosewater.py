"""Rosewater is a command line app for keeping track of the books"""
import argparse
import csv
from datetime import datetime
import logging
import os
import sqlite3
import sys
from typing import Type

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


class BookShelf:
    """Class for collection of books"""

    def __init__(self, path_to_database: str) -> None:
        if os.path.exists(path_to_database):
            database = path_to_database
        else:
            database = self.createNewDatabase(path_to_database)
        self.db = database

    @classmethod
    def createNewDatabase(cls, path_to_database: str) -> str:
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

    def closeDB(self, connection):
        connection.close()

    def addToDatabase(self, Book):
        connection, cursor = self.getConnection()
        cursor.execute(
            """INSERT into "bookshelf" (title, author, isbn, num_of_pages, pub_date, publisher, open_lib_work_key) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                Book.title,
                Book.author,
                Book.isbn,
                Book.num_of_pages,
                Book.pub_date,
                Book.publisher,
                Book.open_lib_work_key,
            ),
        )
        connection.commit()
        self.closeDB(connection)

    def exportToCSV(self, PATH_TO_CSV: str):
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


class Book:
    """Class for individual book entries"""

    def __init__(self, book_metadata):
        """Create new book object from book metadata"""
        self.title = book_metadata[0]["title"]
        self.author = book_metadata[0]["author"]
        self.isbn = book_metadata[0]["isbn"]
        self.num_of_pages = book_metadata[0]["num_of_pages"]
        self.pub_date = book_metadata[0]["pub_date"]
        self.publisher = book_metadata[0]["publisher"]
        self.open_lib_work_key = book_metadata[0]["work_key"]

    def __repr__(self):
        """Return a string of the expression that creates the object"""
        return f"{self.__class__.qualname__}"

    def __str__(self):
        """Return human readable string"""
        return f"{self.title} by {self.author}, published in {self.pub_date} by {self.publisher}"

    def __iter__(self):
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

    def write_to_csv(self):
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


def open_lib_search(isbn):
    """get data using general open library search api"""
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


def validate_isbn(isbn):
    """Test for valid isbn"""
    # isbn = isbn.strip(isbn)
    check = isbn.isdigit()
    if check:
        length = len(isbn)
        if length == 10 or length == 13:
            return True
    else:
        return False


def check_book(book: Type[Book]):
    check = input(f"Is {book} the book you want to add to your bookshelf? y/n: ")

    if check[0].lower() == "y":
        return True
    else:
        logging.critical("Incorrect book. Exiting program.")
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
            book_metadata = open_lib_search(isbn)

            if not book_metadata:
                logging.critical("No results found for %s", isbn)

            logging.debug(book_metadata)

            book = Book(book_metadata)

            logging.info(book)

            check = check_book(book)

            if check:
                logging.info("Writing %s to csv", book.isbn)
                book.write_to_csv()

                logging.info("Establishing Bookshelf class")
                bookshelf = BookShelf(PATH_TO_DATABASE)

                logging.info("Writing %s to bookshelf", book.isbn)
                bookshelf.addToDatabase(book)
        elif args.export:
            logging.info("Establishing Bookshelf class")
            bookshelf = BookShelf(PATH_TO_DATABASE)

            bookshelf.exportToCSV(PATH_TO_CSV)
        else:
            logging.info("Something else")


if __name__ == "__main__":
    main()
