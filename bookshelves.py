"""bookshelves is a command line app for keeping track of books
you have read. It keeps them in a sqlite3 database, which can be
exported and imported to a csv"""
import argparse
import csv
from datetime import datetime
from collections import defaultdict
import logging
import os
import sqlite3
import sys
from typing import Dict, Type

import requests

logging.basicConfig(
    level=logging.INFO, format=" %(asctime)s -  %(levelname)s -  %(message)s"
)

DATA_FOLDER = "data"

PATH_TO_DATABASE = os.path.join(DATA_FOLDER, "bookshelves.db")

parser = argparse.ArgumentParser()

parser.add_argument("-a", "--add", help="Add to database", nargs="+")
parser.add_argument(
    "-e", "--export", action="store_true", help="Export database to csv"
)
parser.add_argument("-i", "--import_csv", help="Import csv file to database")
parser.add_argument(
    "-t", "--top_ten", action="store_true", help="View top 10 most read books ten books"
)


class Book:
    """Class for individual book entries"""

    def __init__(self, book_metadata: Dict[str, str]):
        """Create new book object from book metadata or from isbn.
        If created via isbn call will be made to open library.
        Book metadata dictionary must be created from either
        the bookshelves class database schema
        or imported from the open library api.
        The init method fills out data types that may not have been
        passed across from the API call but would have been passed
        across from a csv import."""
        if type(book_metadata) is not dict:
            result = self.validateISBN(book_metadata)
            if not result:
                logging.critical("Invalid ISBN passed")
                terminate_program()
            else:
                # book metadata fetched via isbn will always return one result
                # but result will always be a list
                # index 0 gets actual metadata
                book_metadata = self.openLibIsbnSearch(book_metadata)

        if book_metadata is None:
            logging.critical("No book metadata found")
            terminate_program()

        book_metadata_default_schema = self.setDefaultDict()
        book_metadata_default_schema.update(book_metadata)

        book_metadata = book_metadata_default_schema

        self.id = book_metadata["id"]
        self.title = book_metadata["title"]
        self.primary_author_key = book_metadata["primary_author_key"]
        self.primary_author = book_metadata["primary_author"]
        self.secondary_authors_keys = book_metadata["secondary_authors_keys"]
        self.secondary_authors = book_metadata["secondary_authors"]
        self.isbn_13 = book_metadata["isbn_13"]
        self.edition_publish_date = book_metadata["edition_publish_date"]
        self.number_of_pages = book_metadata["number_of_pages"]
        self.publisher = book_metadata["publisher"]
        self.open_lib_key = book_metadata["open_lib_key"]
        self.goodreads_identifier = book_metadata["goodreads_identifier"]
        self.librarything_identifier = book_metadata["librarything_identifier"]
        self.date_added = book_metadata["date_added"]
        self.date_finished = book_metadata["date_finished"]
        self.comments = book_metadata["comments"]

        # these are stored for debugging
        self.complete_book_metadata = book_metadata

        logging.debug("Book init, complete metadata: %s", self.complete_book_metadata)

        logging.debug(self.__repr__())

    @staticmethod
    def setDefaultDict():
        """Uses collections default dictionary method
        to set default_dict values for the default
        book metadata schema. This allows the user to update
        the comments and date finished values which are unique to the user
        and means any missing values default to an empty string."""

        # define datestamp to be used for default date values
        # if dates are not supplied
        datestamp = datetime.today().strftime("%Y-%m-%d")

        default_dict = {
            "id": "",
            "title": "",
            "primary_author_key": "",
            "primary_author": "",
            "secondary_authors_keys": "",
            "secondary_authors": "",
            "isbn_13": "",
            "edition_publish_date": "",
            "number_of_pages": "",
            "publisher": "",
            "open_lib_key": "",
            "goodreads_identifier": "",
            "librarything_identifier": "",
            "date_added": datestamp,
            "date_finished": datestamp,
            "comments": "",
        }

        book_metadata_default_schema = defaultdict()
        book_metadata_default_schema.update(default_dict)
        return book_metadata_default_schema

    @classmethod
    def openLibIsbnSearch(cls, isbn: str) -> Dict[str, str] | None:
        """get data back from open library api via isbn"""
        url = f"https://openlibrary.org/isbn/{isbn}.json"

        logging.debug("Request url: %s", url)

        # get response as json
        response = requests.get(url)
        open_lib_data = response.json()

        try:
            # authors goes via different page
            authors_open_lib_keys = open_lib_data["authors"]
        except KeyError as e:
            logging.critical("No author for %s in open library: %s", isbn, e)
            book_metadata = None
            return book_metadata

        secondary_authors = ""
        secondary_authors_keys = ""

        if len(authors_open_lib_keys) == 1:
            author_key = authors_open_lib_keys[0]["key"]
            author_url = "https://openlibrary.org" + author_key + ".json"

            response = requests.get(author_url)
            response_dict = response.json()
            author = response_dict["name"]
        else:
            for count, author in enumerate(authors_open_lib_keys):
                if count == 0:
                    continue
                author_key = authors_open_lib_keys[count]["key"]

                author_url = "https://openlibrary.org" + author_key + ".json"

                response = requests.get(author_url)
                response_dict = response.json()
                author = response_dict["name"]

                secondary_authors = secondary_authors + ", " + author
                secondary_authors_keys = secondary_authors_keys + ", " + author_key

        # not every title has goodreads / librarything identifiers
        # so set to blank if they don't exist
        try:
            goodreads_identifier = open_lib_data["identifiers"]["goodreads"][0]
        except KeyError:
            goodreads_identifier = ""
        try:
            librarything_identifier = open_lib_data["identifiers"]["librarything"][0]
        except KeyError:
            librarything_identifier = ""
        try:
            number_of_pages = open_lib_data["number_of_pages"]
        except KeyError:
            number_of_pages = ""

        logging.debug("complete_open_lib_data: %s", open_lib_data)
        # values that are indexed on 0 are returned as list
        # but should only get one result when searching via isbn
        try:
            book_metadata = {
                "title": open_lib_data["title"],
                "primary_author_key": authors_open_lib_keys[0]["key"],
                "primary_author": author,
                "secondary_authors_keys": secondary_authors_keys,
                "secondary_authors": secondary_authors,
                "isbn_13": isbn,
                "edition_publish_date": open_lib_data["publish_date"],
                "number_of_pages": number_of_pages,
                "publisher": open_lib_data["publishers"][0],
                "open_lib_key": open_lib_data["key"],
                "goodreads_identifier": goodreads_identifier,
                "librarything_identifier": librarything_identifier,
            }
        except Exception as e:
            logging.critical("Key value not found for %s", isbn, e)
            book_metadata = None
            return book_metadata

        logging.debug("Book_metadata returned: %s", book_metadata)

        return book_metadata

    @staticmethod
    def validateISBN(isbn: str) -> bool:
        """Test for valid isbn"""
        isbn = isbn.strip()

        if isbn.isdigit() is False:
            logging.critical("ISBN contains characters that aren't numbers")
            return False
        else:
            if len(isbn) == 13:
                return True
            else:
                logging.info("ISBN is invalid length")
                return False

    def addComments(self):
        """Check to add comments to book object"""
        comments = input(
            f"""Would you like to add any comments for {self}?

Press enter to skip. Otherwise type comments below:

"""
        )
        self.comments = comments

    def __repr__(self):
        """Return a string of the expression that creates the object"""
        return f"{self.__class__.__qualname__}({self.complete_book_metadata})"

    def __str__(self):
        """Return human readable string"""
        return f"{self.title} by {self.primary_author}, edition published in {self.edition_publish_date}"

    def __iter__(self):
        """Create iterable of book metadata."""
        return iter(
            [
                self.id,
                self.title,
                self.primary_author_key,
                self.primary_author,
                self.secondary_authors_keys,
                self.secondary_authors,
                self.isbn_13,
                self.edition_publish_date,
                self.number_of_pages,
                self.publisher,
                self.open_lib_key,
                self.goodreads_identifier,
                self.librarything_identifier,
                self.date_added,
                self.date_finished,
                self.comments,
            ]
        )


class Bookshelves:
    """Class for database of books"""

    def __init__(self, path_to_database: str):
        """Create new bookshelves database object"""
        self.path_to_database = path_to_database

        if os.path.exists(path_to_database):
            database = path_to_database
        else:
            database = self.createNewDatabase(path_to_database)

        self.db = database

        logging.debug(self.__repr__())

    @classmethod
    def createNewDatabase(cls, path_to_database: str) -> str:
        """Create new database file with standard rows."""
        connection = sqlite3.connect(path_to_database)
        cursor = connection.cursor()
        cursor.execute(
            "CREATE TABLE bookshelves(id integer primary key autoincrement, title, primary_author_key, primary_author, secondary_authors_keys, secondary_authors,isbn_13, edition_publish_date, number_of_pages, publisher, open_lib_key, goodreads_identifier, librarything_identifier, date_added, date_finished, comments)"
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
        logging.info("Inserting %s into %s", book, PATH_TO_DATABASE)
        connection, cursor = self.getConnection()

        cursor.execute(
            """INSERT into "bookshelves" (title, primary_author_key, primary_author, secondary_authors_keys, secondary_authors,isbn_13, edition_publish_date, number_of_pages, publisher, open_lib_key, goodreads_identifier, librarything_identifier, date_added, date_finished, comments) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                book.title,
                book.primary_author_key,
                book.primary_author,
                book.secondary_authors_keys,
                book.secondary_authors,
                book.isbn_13,
                book.edition_publish_date,
                book.number_of_pages,
                book.publisher,
                book.open_lib_key,
                book.goodreads_identifier,
                book.librarything_identifier,
                book.date_added,
                book.date_finished,
                book.comments,
            ),
        )
        connection.commit()
        self.closeDB(connection)

    def checkIfIDExists(self, id_value: str) -> bool:
        """Used to check if an ID value exists to avoid
        duplicates when importing from csv."""
        connection, cursor = self.getConnection()
        query = cursor.execute(
            """SELECT id FROM bookshelves WHERE id = ?""", (id_value,)
        )
        # if anything is returned then id exists
        result = query.fetchone()

        if result:
            return True
        else:
            return False

    def updateValues(self, book: Book):
        """Update values in database to match import"""
        logging.info("Updating values for %s in %s", book, self.db)
        logging.debug("New values for book: %s", book.complete_book_metadata)
        connection, cursor = self.getConnection()

        cursor.execute(
            """UPDATE "bookshelves" SET title = ?, primary_author_key = ?, primary_author = ?, secondary_authors_keys = ?, secondary_authors = ?, isbn_13 = ?, edition_publish_date = ?, number_of_pages = ?, publisher = ?, open_lib_key = ?, goodreads_identifier = ?, librarything_identifier = ?, date_added = ?, date_finished = ?, comments = ? WHERE id = ?""",
            (
                book.title,
                book.primary_author_key,
                book.primary_author,
                book.secondary_authors_keys,
                book.secondary_authors,
                book.isbn_13,
                book.edition_publish_date,
                book.number_of_pages,
                book.publisher,
                book.open_lib_key,
                book.goodreads_identifier,
                book.librarything_identifier,
                book.date_added,
                book.date_finished,
                book.comments,
                book.id,
            ),
        )
        connection.commit()
        self.closeDB(connection)

    def exportToCSV(self, path_to_csv: str = ""):
        """Export database to csv file."""
        if path_to_csv == "":
            datestamp = datetime.today().strftime("%Y%m%d")
            output_filename = "bookshelves-" + datestamp + ".csv"
            output_filepath = os.path.join(DATA_FOLDER, output_filename)
        else:
            output_filepath = path_to_csv

        connection, cursor = self.getConnection()
        bookshelves = cursor.execute("""SELECT * from bookshelves""")

        logging.info("Writing to %s", output_filepath)

        default_header_rows = list(Book.setDefaultDict().keys())

        with open(output_filepath, "w", encoding="utf-8", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(default_header_rows)
            for book in bookshelves:
                logging.info("Writing %s to csv", book["title"])
                writer.writerow(book)

        self.closeDB(connection)

    def importFromCSV(self, import_csv_file: str):
        """Import a csv file to bookshelves database."""
        check = input(
            """If your CSV has the following columns in order,
then it will be directly imported into the database:

id
title
primary_author_key
primary_author
secondary_authors_keys
secondary_authors
isbn_13
edition_publish_date
number_of_pages
publisher
open_lib_key
goodreads_identifier
librarything_identifier
date_added
date_finished
comments

Otherwise, it must have a column titled isbn_13.
And an isbn listed for each title and the book metadata will be fetched from the open library.

Would you like to continue? y/n: "
"""
        )

        if confirm_user_input(check):
            fail_count = 0
            success_count = 0

            with open(import_csv_file, "r", encoding="utf-8", newline="") as csv_file:
                reader = csv.DictReader(csv_file)

                default_header_rows = list(Book.setDefaultDict().keys())

                # if headings on csv match default database schema
                # import directly from csv
                if reader.fieldnames == default_header_rows:
                    logging.info("Importing data directly from csv file")

                    books_metadata = list(reader)

                    for book_metadata in books_metadata:
                        # must explicitly pass book metadata to book obj
                        book = Book(book_metadata)

                        result = self.checkIfIDExists(book.id)

                        if result:
                            logging.info(
                                "id already exists in database for: %s. Id value: %s",
                                book_metadata["title"],
                                book_metadata["id"],
                            )
                            # id already exists
                            self.updateValues(book)
                        else:
                            self.addToDatabase(book)
                            success_count += 1

                else:
                    logging.info("Getting data from open library")

                    for row in reader:
                        isbn = row["isbn_13"]

                        if Book.validateISBN(isbn):
                            try:
                                book_metadata = Book.openLibIsbnSearch(isbn)
                            except Exception as e:
                                logging.critical(
                                    "Except when fetching data for %s. Error message: %s",
                                    isbn,
                                    e,
                                )
                                self.writeFailedImportsToFile(row, e)
                                fail_count += 1
                                continue

                            book = Book(book_metadata)

                            # if spreadsheet includes user defined
                            # comments and date finished rows
                            # then update values for book
                            # before adding to database
                            try:
                                comments = row["comments"]
                                book.comments = comments
                            except KeyError:
                                pass

                            try:
                                date_finished = row["date_finished"]
                                book.date_finished = date_finished
                            except KeyError:
                                pass

                            self.addToDatabase(book)
                            success_count += 1
                        else:
                            error_message = "Invalid ISBN passed"
                            self.writeFailedImportsToFile(row, error_message)
                            logging.critical("Invalid ISBN passed: %s", isbn)
                            fail_count += 1
                            continue
                logging.info("%s number of titles successfully imported", success_count)
                logging.info("With %s number of titles failed import", fail_count)
        else:
            terminate_program()

    def writeFailedImportsToFile(self, row, error_message):
        """Used to write failed imports from import csv
        to failed imports file"""
        failed_imports_path = os.path.join("data", "failed-imports.csv")

        # add error message to row dictionary
        row["error_message"] = str(error_message)

        if os.path.exists(failed_imports_path) is False:
            with open(failed_imports_path, "w", encoding="utf-8", newline="") as output:
                writer = csv.DictWriter(output, row.keys())
                writer.writeheader()
                writer.writerow(row)
        else:
            with open(failed_imports_path, "a", encoding="utf-8", newline="") as output:
                writer = csv.DictWriter(output, row.keys())
                writer.writerow(row)

    def getTopTenBooks(self):
        """Get top ten most read books in database"""

        connection, cursor = self.getConnection()
        top_ten = cursor.execute(
            """SELECT *, count(title) FROM "bookshelves" GROUP BY title ORDER by count(title) DESC LIMIT 10"""
        )
        print("\nTOP TEN")
        print("~~~~~~~")
        for row in top_ten:
            count = row[-1]
            book = Book(row)
            print(f"{book} has been read {count} times.")

    def __repr__(self):
        """Return a string of the expression that creates the object"""
        return f"{self.__class__.__qualname__}({self.path_to_database})"


def validate_date(date: str):
    """Validate given string and return true/false
    depending on if string is a valid date"""
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        logging.info("Invalid date given")
        logging.info("Format must be yyyy-mm-dd")
        return False


def confirm_user_input(check: str):
    """Used to check user input for yes or no."""
    if check[0].lower() == "y":
        return True
    else:
        terminate_program()


def usage():
    logging.info(
        """
Usage:
    bookshelves.py [args] [opt-book-isbn]
    # Add book to database:
    bookshelves.py -a [valid-isbn]
    # Add book to database with optional args:
    bookshelves.py -a [valid-isbn] [date-book-finished: yyyy-mm-dd] ["comments on book"]
    bookshelves.py -a [valid-isbn]
    # import to database from csv
    bookshelves.py -i [path-to-csv]
    # export database to csv
    bookshelves.py -e
    # view top ten books
    bookshelves.py -t
    """
    )


def terminate_program():
    """Wrapper function to quickly and clearly exit program"""
    logging.critical("Terminating program")
    sys.exit(1)


def main():
    if (len(sys.argv)) == 1:
        logging.info("Invalid usage: no args passed\n")
        usage()
        terminate_program()
    else:
        args = parser.parse_args()
        if args.add:
            isbn = None
            date_finished = None
            comments = None

            for arg in args.add:
                if Book.validateISBN(arg) is True:
                    isbn = arg
                elif validate_date(arg) is True:
                    date_finished = arg
                else:
                    comments = arg

            if isbn is None:
                logging.critical("No valid ISBN passed for adding book to database")
                terminate_program()

            logging.info("searching for %s", isbn)

            book = Book(isbn)

            logging.info(book)

            check = input(
                f"Is {book} the book you want to add to your bookshelves? y/n: "
            )

            check = confirm_user_input(check)

            if comments is None:
                logging.info("Checking for user comments")
                book.addComments()
            else:
                logging.info("Assigning user comments from args passed")
                book.comments = comments

            if date_finished:
                logging.info("Assigning date finished for book from args passed")
                book.date_finished = date_finished

            if check:
                logging.info("Establishing Bookshelves class")
                bookshelves = Bookshelves(PATH_TO_DATABASE)

                logging.info("Writing %s to bookshelves", book.isbn_13)
                bookshelves.addToDatabase(book)
        elif args.export:
            logging.info("Establishing bookshelves class")
            bookshelves = Bookshelves(PATH_TO_DATABASE)

            bookshelves.exportToCSV()
        elif args.import_csv:
            import_csv_filepath = args.import_csv

            if os.path.exists(import_csv_filepath) is False:
                logging.critical("CSV filepath does not exist: %s", import_csv_filepath)
                terminate_program()

            bookshelves.importFromCSV(import_csv_filepath)
        elif args.top_ten:
            bookshelves = Bookshelves(PATH_TO_DATABASE)

            bookshelves.getTopTenBooks()

        else:
            logging.critical("Invalid args given.")
            terminate_program()


if __name__ == "__main__":
    main()
