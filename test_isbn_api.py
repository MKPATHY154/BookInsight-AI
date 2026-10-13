
import requests

url = "https://openlibrary.org/search.json"

params = {
    "q": "subject:fiction",
    "fields": "key,title,author_name,isbn",
    "limit": 10
}

try:
    response = requests.get(
        url,
        params=params,
        timeout=30,
        headers={"User-Agent": "BookInsightAI/1.0"}
    )
    response.raise_for_status()

    data = response.json()
    books = data.get("docs", [])

    print("Books returned:", len(books))

    for book in books:
        print("Title:", book.get("title"))
        print("ISBN:", book.get("isbn", []))
        print("-" * 40)

except (requests.RequestException, ValueError) as error:
    print("API error:", error)
