
import sqlite3
import requests
import time

DATABASE_PATH = "data/books.db"
API_URL = "https://openlibrary.org/search.json"

connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()

cursor.execute("""
    SELECT open_library_id, title
    FROM open_library_books
    WHERE isbn IS NULL OR isbn = ''
""")

books = cursor.fetchall()

print("Books to check:", len(books))

updated = 0
failed = 0

try:
    for index, (book_id, title) in enumerate(books, start=1):
        try:
            params = {
                "q": "title:" + title,
                "fields": "key,title,isbn",
                "limit": 10
            }

            response = requests.get(
                API_URL,
                params=params,
                timeout=20,
                headers={"User-Agent": "BookInsightAI/1.0"}
            )
            response.raise_for_status()

            results = response.json().get("docs", [])

            matching_book = next(
                (
                    item for item in results
                    if item.get("key") == book_id
                    and item.get("isbn")
                ),
                None
            )

            if matching_book:
                isbn = matching_book["isbn"][0]

                cursor.execute("""
                    UPDATE open_library_books
                    SET isbn = ?
                    WHERE open_library_id = ?
                """, (isbn, book_id))

                updated += 1

            if index % 25 == 0:
                connection.commit()
                print(
                    "Checked:", index,
                    "| ISBNs updated:", updated,
                    "| Failed requests:", failed
                )

            time.sleep(0.2)

        except (requests.RequestException, ValueError) as error:
            failed += 1
            print("Request failed for:", title, "-", error)

    connection.commit()

finally:
    connection.close()

print("\nISBN update finished.")
print("ISBNs updated:", updated)
print("Books still without ISBN:", len(books) - updated)
print("Failed requests:", failed)
