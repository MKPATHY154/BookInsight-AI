
import unittest

from data_cleaner import clean_books


class TestDataCleaner(unittest.TestCase):

    def test_removes_duplicate_books(self):
        books = [
            {
                "title": "Test Book",
                "price": "£19.99",
                "rating": "Five",
                "availability": "In stock",
                "product_url": "https://example.com/book"
            },
            {
                "title": "Test Book",
                "price": "£19.99",
                "rating": "Five",
                "availability": "In stock",
                "product_url": "https://example.com/book"
            }
        ]

        result = clean_books(books)

        self.assertEqual(len(result), 1)

    def test_converts_price_to_number(self):
        books = [
            {
                "title": "Test Book",
                "price": "Â£19.99",
                "rating": "Five",
                "availability": "In stock",
                "product_url": "https://example.com/book"
            }
        ]

        result = clean_books(books)

        self.assertAlmostEqual(result.iloc[0]["price"], 19.99)

    def test_strips_title_whitespace(self):
        books = [
            {
                "title": " Test Book ",
                "price": "£19.99",
                "rating": "Five",
                "availability": "In stock",
                "product_url": "https://example.com/book"
            }
        ]

        result = clean_books(books)

        self.assertEqual(result.iloc[0]["title"], "Test Book")


if __name__ == "__main__":
    unittest.main()

