# Bookshelves

Bookshelves is a command line app to keep track of books you have read. The books are stored in a sqlite3 database, which can be exported to a csv. You can re-import csv data, to update values in the database.

Bookshelves is for people who:
* like using the command line
* keep track of the books they read
* like being the responsible for their own data
* don't mind typing the ISBN value for a book

## Book metadata schema

Book metadata is fetched from the [Open Library](https://openlibrary.org/) using the isbn 13 value for the book.

Bookshelves collects the following book metadata values:

* title
* primary_author_key
* primary_author
* secondary_authors_keys
* secondary_authors
* isbn_13
* edition_publish_date
* number_of_pages
* publisher
* open_lib_key
* goodreads_identifier
* librarything_identifier
* date_added
* date_finished
* comments

The date finished and the comments sections can be personalised by the user. Likewise if any metadata values are not filled out via the open library call then these values can be updated by the user. Once a book has an id value in the database, its values will be updated by an import of a csv.

## Why ISBN?

The ISBN 13 is the only data value that is used to fetch data from the open library. This has been chosen because book metadata can be confusing and using the ISBN 13 value is the best way to make sure your result is accurate.

Every book has an ISBN and it is normally added to the bar code of a physical book, and failing that it can be found in the front matter.

## Requirements

Bookshelves was developed using python 3.11.0. The only non-standard python library required is [requests 2.31.0](https://github.com/psf/requests).

Everything has been kept in one file for simplicity and portability.

## Usage

By default your database will be created in /data folder relative to the bookshelves.py location.

### Add single book to database

```
python bookshelves.py -a [valid-isbn]

# add book to database with personalised values:
python bookshelves.py -a [valid-isbn] [date-book-finished: yyyy-mm-dd] ["personal comments on book"]
```

### Import to database from csv

```
python bookshelves.py -i [path-to-csv]
```

When importing from csv, if your import file follows the schema in the database then data will be added from the csv for titles that don't yet have a matching id. For titles that do have a matching id, data in the database will be updated with the values in the csv. The ability to bulk update via csv has been added to allow for an easy way to update faulty data, and to personalise the comments and date finished values.

If starting a new csv import that doesn't match the schema in the database then your csv must have a column heading named isbn_13. Imports will not work without an valid ISBN 13 value.

### Export database to csv

```
python bookshelves.py -e
```

This will export the contents of your bookshelves database to a csv file in the /data folder named bookshelves-yyyymmdd.csv.

### View top ten books

```
python bookshelves.py -t
```

As a book can be read and thus added to the database multiple times, this returns a count of your top ten most read titles, with the count being performed on the title value in the database.
