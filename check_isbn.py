
import sqlite3

connection = sqlite3.connect("data/books.db")
cursor = connection.cursor()

cursor.execute("SELECT COUNT(*) FROM open_library_books")
total_books = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*)
    FROM open_library_books
    WHERE isbn IS NOT NULL AND isbn != ''
""")
books_with_isbn = cursor.fetchone()[0]

print("Total Open Library books:", total_books)
print("Books with ISBN:", books_with_isbn)
print("Books without ISBN:", total_books - books_with_isbn)

connection.close()
import sqlite3

connection = sqlite3.connect("data/books.db")
cursor = connection.cursor()

cursor.execute("SELECT COUNT(*) FROM open_library_books")
total = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*)
    FROM open_library_books
    WHERE isbn IS NOT NULL AND isbn != ''
""")
with_isbn = cursor.fetchone()[0]

print("Total books:", total)
print("Books with ISBN:", with_isbn)
print("Books without ISBN:", total - with_isbn)

connection.close()