import argparse
import sys

import requests

parser = argparse.ArgumentParser()

parser.add_argument("-a", "--add", help="Add to database")


def open_lib_search(term):
    """get data using general open library search api"""
    url = "https://openlibrary.org/search.json"

    # create url query
    search_url = url + "?q=" + term + "&limit=20"

    response = requests.get(search_url)
    response_dict = response.json()

    result = []
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
    except KeyError as e:
        # if work doesn't have basic biblographic data ignore it
        print(f"{e}: invalid book")

    result.append(
        {
            "work_key": work_key,
            "title": title,
            "pub_date": first_publish_date,
            "num_of_pages": num_of_pages,
            "author": author,
        }
    )
    return result


def usage():
    print("""
Usage:
    rosewater.py [args] [opt-book-isbn]
    # Add book to datebase:
    rosewater.py -a [valid-isbn]
    """)


def main():
    if (len(sys.argv)) == 1:
        print("Invalid usage: no args passed\n")
        usage()
        sys.exit(1)
    else:
        args = parser.parse_args()
        if args.add:
            isbn = args.add
            print(f"adding {isbn} to database")
            book = open_lib_search(isbn)
            print(book)
        else:
            print("Something else")


if __name__ == "__main__":
    main()
