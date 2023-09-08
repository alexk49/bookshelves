"""Rosewater is a command line app for keeping track of the books"""
import argparse
import logging
import sys

import requests

logging.basicConfig(
    level=logging.DEBUG, format=" %(asctime)s -  %(levelname)s -  %(message)s"
)

# TODO: validate isbn
# TODO: get user to confirm book fetched from open lib
# TODO: commit to sql database
# TODO: convert to csv

parser = argparse.ArgumentParser()

parser.add_argument("-a", "--add", help="Add to database")


class Book:
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
    if (len(sys.argv)) == 1:
        logging.info("Invalid usage: no args passed\n")
        usage()
        sys.exit(1)
    else:
        args = parser.parse_args()
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

        else:
            logging.info("Something else")


if __name__ == "__main__":
    main()
