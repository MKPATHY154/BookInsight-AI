from database import save_books
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from config import BASE_URL, REQUEST_TIMEOUT, REQUEST_DELAY, MAX_PAGES
import time


def scrape_books():
    books = []
    session = requests.Session()

    session.headers.update({
        "User-Agent": "BookInsightAI/1.0 (educational project)"
    })

    page_url = urljoin(BASE_URL, "catalogue/page-1.html")
    page_count = 0

    while page_url and page_count < MAX_PAGES:
        try:
            response = session.get(
                page_url,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            book_cards = soup.select("article.product_pod")

            if not book_cards:
                break

            for card in book_cards:
                title_element = card.select_one("h3 a")
                price_element = card.select_one(".price_color")
                availability_element = card.select_one(
                    ".availability"
                )
                rating_element = card.select_one("p.star-rating")

                if title_element is None or price_element is None:
                    continue

                rating = "Unknown"
                if rating_element:
                    rating_classes = rating_element.get("class", [])
                    rating_words = [
                        word for word in rating_classes
                        if word != "star-rating"
                    ]
                    if rating_words:
                        rating = rating_words[0]

                book = {
                    "title": title_element.get("title", "").strip(),
                    "price": price_element.get_text(strip=True),
                    "rating": rating,
                    "availability": (
                        availability_element.get_text(" ", strip=True)
                        if availability_element else "Unknown"
                    ),
                    "product_url": urljoin(
                        page_url,
                        title_element.get("href", "")
                    )
                }

                books.append(book)

            next_button = soup.select_one("li.next a")

            if next_button:
                page_url = urljoin(
                    page_url,
                    next_button.get("href", "")
                )
            else:
                page_url = None

            page_count += 1

            if page_url and page_count < MAX_PAGES:
                time.sleep(REQUEST_DELAY)

        except requests.RequestException as error:
            print("Scraping error:", error)
            break

    return books

if __name__ == "__main__":
    scraped_books = scrape_books()

    print("Total books scraped:", len(scraped_books))

    if scraped_books:
        save_books(scraped_books)

    for book in scraped_books[:5]:
        print(book)