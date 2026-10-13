from database import save_open_library_books
import requests

OPEN_LIBRARY_URL = "https://openlibrary.org/search.json"


def fetch_open_library_books(target_count=5000):
    books = []
    print("Starting Open Library collection...")
    seen_ids = set()
    page = 9
    page_size = 100

    while len(books) < target_count:
        params = {
    "q": "subject:fiction",
    "fields": "key,title,author_name,first_publish_year,isbn,cover_i",
    "page": page,
    "limit": page_size
}

        try:
            response = requests.get(
                OPEN_LIBRARY_URL,
                params=params,
                timeout=60,
                headers={"User-Agent": "BookInsightAI/1.0"}
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as error:
            print("Open Library request failed:", error)
            break

        results = data.get("docs", [])

        if not results:
            break

        for item in results:
            book_id = item.get("key")
            title = item.get("title")

            if not book_id or not title or book_id in seen_ids:
                continue

            seen_ids.add(book_id)

            authors = item.get("author_name", [])
            isbn_list = item.get("isbn", [])

            books.append({
                "open_library_id": book_id,
                "title": title,
                "author": ", ".join(authors),
                "publication_year": item.get("first_publish_year"),
                "isbn": isbn_list[0] if isbn_list else None,
                "cover_id": item.get("cover_i")
            })

            if len(books) >= target_count:
                break

        print("Unique books collected:", len(books))
        page += 1

    return books


if __name__ == "__main__":
    books = fetch_open_library_books(4200)
    print("Total unique Open Library books:", len(books))

    if books:
        save_open_library_books(books)