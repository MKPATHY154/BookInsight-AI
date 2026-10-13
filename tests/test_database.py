
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(
            Path(self.temp_dir.name) / "test_books.db"
        )

        self.patcher = patch.object(
            database, "DATABASE_PATH", self.db_path
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

    def test_create_database(self):
        database.create_database()

        connection = sqlite3.connect(self.db_path)
        result = connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='books'"
        ).fetchone()
        connection.close()

        self.assertIsNotNone(result)

    def test_save_book(self):
        book = {
            "title": "Test Book",
            "price": "£19.99",
            "rating": "Five",
            "availability": "In stock",
            "product_url": "https://example.com/test-book"
        }

        database.save_books([book])

        connection = sqlite3.connect(self.db_path)
        result = connection.execute(
            "SELECT title, price FROM books"
        ).fetchone()
        connection.close()

        self.assertEqual(result[0], "Test Book")
        self.assertAlmostEqual(result[1], 19.99)

    def test_duplicate_book_updates_existing_record(self):
        book = {
            "title": "Test Book",
            "price": "£19.99",
            "rating": "Five",
            "availability": "In stock",
            "product_url": "https://example.com/test-book"
        }

        database.save_books([book])

        updated_book = book.copy()
        updated_book["price"] = "£15.99"

        database.save_books([updated_book])

        connection = sqlite3.connect(self.db_path)
        result = connection.execute(
            "SELECT COUNT(*), price FROM books"
        ).fetchone()
        connection.close()

        self.assertEqual(result[0], 1)
        self.assertAlmostEqual(result[1], 15.99)


if __name__ == "__main__":
    unittest.main()
