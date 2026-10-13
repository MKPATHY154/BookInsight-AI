
import sqlite3
from config import DATABASE_PATH
from pathlib import Path


def create_database():
    Path(DATABASE_PATH).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price REAL,
            rating TEXT,
            availability TEXT,
            product_url TEXT UNIQUE,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()

    print("Database and books table created successfully.")


def save_books(books):
    create_database()

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    for book in books:
        price_text = (
            book["price"]
            .replace("Â£", "")
            .replace("£", "")
            .strip()
        )

        try:
            price = float(price_text)
        except ValueError:
            price = None

        cursor.execute("""
            INSERT INTO books (
                title, price, rating,
                availability, product_url, last_updated
            )
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(product_url) DO UPDATE SET
                title = excluded.title,
                price = excluded.price,
                rating = excluded.rating,
                availability = excluded.availability,
                last_updated = CURRENT_TIMESTAMP
        """, (
            book["title"],
            price,
            book["rating"],
            book["availability"],
            book["product_url"]
        ))

    connection.commit()
    connection.close()

    print("Books saved successfully:", len(books))

def save_open_library_books(books):
    create_database()

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS open_library_books (
            open_library_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            publication_year INTEGER,
            isbn TEXT,
            cover_id INTEGER
        )
    """)

    for book in books:
        cursor.execute("""
            INSERT OR REPLACE INTO open_library_books (
                open_library_id,
                title,
                author,
                publication_year,
                isbn,
                cover_id
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            book["open_library_id"],
            book["title"],
            book["author"],
            book["publication_year"],
            book["isbn"],
            book["cover_id"]
        ))

    connection.commit()
    connection.close()

    print("Open Library books saved:", len(books))
