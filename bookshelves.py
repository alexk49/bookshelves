"""bookshelves is a command line app for keeping track of the books"""
import argparse
import csv
from datetime import datetime
import logging
import os
import sqlite3
import sys
from typing import Dict, List, Optional, Type

import requests

logging.basicConfig(
    level=logging.DEBUG, format=" %(asctime)s -  %(levelname)s -  %(message)s"
)

DATA_FOLDER = "data"

PATH_TO_DATABASE = os.path.join(DATA_FOLDER, "bookshelves.db")
PATH_TO_CSV = os.path.join(DATA_FOLDER, "bookshelves.csv")

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

    def __init__(
        self,
        book_metadata: Optional[Dict[str, str]] = None,
        isbn: Optional[str] = None,
    ):
        """Create new book object from book metadata or from isbn.
        If created via isbn call will be made to open library.
        Book metadata dictionary must be created from either
        the bookshelves class database schema
        or imported from the open library api.
        The init method fills out data types that may not have been
        passed across from the API call but would have been passed
        across from a csv import."""
        logging.debug("Init for Book class")

        # define datestamp to be used for default date values
        # if dates not supplied
        datestamp = datetime.today().strftime("%Y-%m-%d")

        if book_metadata is None and isbn is None:
            logging.critical("No valid args passed for book object")
            terminate_program()

        logging.debug("ISBN passed to class: %s", isbn)
        logging.debug("book metadata passed to class: %s", book_metadata)

        if book_metadata is None:
            if self.validateISBN(isbn) is False:
                logging.critical("Invalid ISBN passed")
                terminate_program()

            # book metadata fetched via isbn will always return one result
            # but result will always be a list
            # index 0 gets actual metadata
            book_metadata = self.openLibSearch(isbn)[0]

        logging.debug(book_metadata)

        if book_metadata is None:
            logging.critical("No book metadata found")
            terminate_program()

        try:
            # keys from csv import
            self.title = book_metadata["title"]
            self.author = book_metadata["author"]
            self.isbn = book_metadata["isbn"]
            self.num_of_pages = book_metadata["number_of_pages"]
            self.pub_date = book_metadata["publication_date"]
            self.publishers = book_metadata["publishers"]
            self.open_lib_work_key = book_metadata["open_lib_key"]

        except KeyError:
            # keys from open lib import
            self.title = book_metadata["title"]
            self.author = book_metadata["author"]
            self.isbn = book_metadata["isbn"]
            self.num_of_pages = book_metadata["num_of_pages"]
            self.pub_date = book_metadata["pub_date"]
            self.publishers = book_metadata["publisher"]
            self.open_lib_work_key = book_metadata["work_key"]

        try:
            # if no comments field set to blank
            # data from the open library won't ever have comments
            # so this is neccessary for compatability
            self.comments = book_metadata["comments"]
        except KeyError:
            self.comments = ""

        try:
            self.date_added = book_metadata["date_added"]
        except KeyError:
            self.date_added = datestamp
        try:
            self.date_finished = book_metadata["date_finished"]
        except KeyError:
            self.date_finished = datestamp

        # keep original book metadata
        # and org isbn passed
        # passed for debugging
        self.book_metadata = book_metadata
        self.creation_isbn = isbn

        logging.debug(self.__repr__())

    @classmethod
    def openLibSearch(cls, isbn: str) -> List[Dict[str, str]]:
        """Get book data using general open library search api."""
        url = "https://openlibrary.org/search.json"

        # create url query
        search_url = url + "?q=" + isbn + "&limit=20"

        response = requests.get(search_url)
        response_dict = response.json()

        results = []
        num = 0

        try:
            # get basic biblographic data
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

            publishers = response_dict["docs"][num]["publisher"]

            # handle multiple publishers
            if len(publishers) == 1:
                publishers = publishers[0]
            else:
                publishers = ", ".join(publishers)

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
                "publisher": publishers,
            }
        )

        return results

    @staticmethod
    def validateISBN(isbn: str) -> bool:
        """Test for valid isbn"""
        logging.debug(isbn)
        logging.debug(type(isbn))

        isbn = isbn.strip()

        if isbn.isdigit() is False:
            logging.critical("ISBN contains characters that aren't numbers")
            return False
        else:
            length = len(isbn)
            if length == 10 or length == 13:
                return True
            else:
                logging.info("ISBN is invalid length")
                logging.debug(len(isbn))
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
        return (
            f"{self.__class__.__qualname__}({self.creation_isbn}, {self.book_metadata})"
        )

    def __str__(self):
        """Return human readable string"""
        return f"{self.title} by {self.author}, published in {self.pub_date}"

    def __iter__(self):
        """Create iterable of book metadata."""
        return iter(
            [
                self.title,
                self.author,
                self.isbn,
                self.num_of_pages,
                self.pub_date,
                self.publishers,
                self.open_lib_work_key,
                self.comments,
                self.date_added,
                self.date_finished,
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
                    "number_of_pages",
                    "publication_date",
                    "publishers",
                    "open_lib_key",
                    "comments",
                ]
            )
            writer.writerow(self)


class Bookshelves:
    """Class for database of books"""

    def __init__(self, path_to_database: str):
        """Create new bookshelves database object"""
        logging.debug("Init for Bookshelves class")
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
            "CREATE TABLE bookshelves(id integer primary key autoincrement, title, author, isbn, number_of_pages, publication_date, publishers, open_lib_key, date_added, date_finished, comments)"
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

        logging.debug(book.comments)
        logging.debug(type(book.comments))

        cursor.execute(
            """INSERT into "bookshelves" (title, author, isbn, number_of_pages, publication_date, publishers, open_lib_key, comments, date_added, date_finished) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                book.title,
                book.author,
                book.isbn,
                book.num_of_pages,
                book.pub_date,
                book.publishers,
                book.open_lib_work_key,
                book.comments,
                book.date_added,
                book.date_finished,
            ),
        )
        connection.commit()
        self.closeDB(connection)

    def exportToCSV(self, PATH_TO_CSV: str):
        """Export database to csv file."""
        connection, cursor = self.getConnection()
        bookshelves = cursor.execute("""SELECT * from bookshelves""")

        logging.debug(bookshelves)
        logging.debug(type(bookshelves))

        datestamp = datetime.today().strftime("%Y%m%d")

        output_filename = "bookshelves-" + datestamp + ".csv"
        output_filepath = os.path.join(DATA_FOLDER, output_filename)

        logging.info("Writing to %s", output_filepath)

        with open(output_filepath, "w") as output:
            writer = csv.writer(output)
            writer.writerow(
                [
                    "id",
                    "title",
                    "author",
                    "isbn",
                    "number_of_pages",
                    "publication_date",
                    "publishers",
                    "open_lib_key",
                    "date_added",
                    "date_finished",
                    "comments",
                ]
            )
            for book in bookshelves:
                logging.info("Writing %s to csv", book["title"])
                writer.writerow(book)

        self.closeDB(connection)

    def importFromCSV(self, import_csv_file: str):
        """Import a csv file to bookshelves database."""
        check = input(
            """If your CSV has the following columns in order,
then it will be directly imported into the database:

title,
author,
isbn,
number_of_pages,
publication_date,
publishers,
open_lib_key,
date_added,
date_finished
comments,

Otherwise, it must have a column titled isbn.
And an isbn listed for each title and the book metadata will be fetched from the open library.

Example schema:

isbn
978-etc
978-etc

Would you like to continue? y/n: "
"""
        )

        if confirm_user_input(check):
            bookshelves = Bookshelves(PATH_TO_DATABASE)

            columns_list = [
                "title",
                "author",
                "isbn",
                "number_of_pages",
                "publication_date",
                "publishers",
                "open_lib_key",
                "date_added",
                "date_finished",
                "comments",
            ]

            with open(import_csv_file, "r") as csv_file:
                reader = csv.DictReader(csv_file)

                logging.debug("Headings: %s ", reader.fieldnames)
                # if headings on csv match default database schema
                # import directly from csv
                if reader.fieldnames == columns_list:
                    logging.info("Importing data directly from csv file")

                    books_metadata = list(reader)

                    logging.debug(books_metadata)
                    logging.debug(books_metadata[0]["title"])

                    for book_metadata in books_metadata:
                        # must explicitly pass book metadata to book obj
                        book = Book(book_metadata=book_metadata)

                        logging.debug(type(book))

                        bookshelves.addToDatabase(book)

                else:
                    logging.info("Getting data from open library")

                    for row in reader:
                        isbn = row["isbn"]
                        logging.debug(isbn)
                        logging.debug(type(isbn))

                        results = Book.openLibSearch(isbn)

                        # open library returns results as list of dictionaries
                        # if searching by isbn you will only get one result
                        # but you must still access the data via index
                        book_metadata = results[0]
                        logging.debug(book_metadata)

                        book = Book(book_metadata)
                        logging.debug(book)

                        bookshelves.addToDatabase(book)
        else:
            terminate_program()

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
    logging.debug(sys.argv)
    if (len(sys.argv)) == 1:
        logging.info("Invalid usage: no args passed\n")
        usage()
        terminate_program()
    else:
        args = parser.parse_args()
        logging.debug(args)
        if args.add:
            logging.debug(args.add)

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
                logging.debug(args.add)
                terminate_program()

            logging.info("searching for %s", isbn)

            # must explicitly give isbn
            # when creating book obj from single isbn
            book = Book(isbn=isbn)

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

            if date_finished is not None:
                logging.info("Assigning date finished for book from args passed")
                book.date_finished = date_finished

            if check:
                logging.info("Writing %s to csv", book.isbn)
                book.writeToCSV()

                logging.info("Establishing Bookshelves class")
                bookshelves = Bookshelves(PATH_TO_DATABASE)

                logging.info("Writing %s to bookshelves", book.isbn)
                bookshelves.addToDatabase(book)
        elif args.export:
            logging.info("Establishing bookshelves class")
            bookshelves = Bookshelves(PATH_TO_DATABASE)

            bookshelves.exportToCSV(PATH_TO_CSV)
        elif args.import_csv:
            logging.debug(args.import_csv)
            import_csv_filepath = args.import_csv
            if os.path.exists(import_csv_filepath) is False:
                logging.critical("CSV filepath does not exist: %s", import_csv_filepath)
                terminate_program()

            bookshelves = Bookshelves(PATH_TO_DATABASE)

            bookshelves.importFromCSV(import_csv_filepath)
        elif args.top_ten:
            logging.debug(args.top_ten)

            bookshelves = Bookshelves(PATH_TO_DATABASE)

            bookshelves.getTopTenBooks()

        else:
            logging.critical("Invalid args given.")
            terminate_program()


if __name__ == "__main__":
    main()
