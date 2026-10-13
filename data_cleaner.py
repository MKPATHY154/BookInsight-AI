
import pandas as pd


def clean_books(books):
    df = pd.DataFrame(books)

    if df.empty:
        return df

    df = df.dropna(subset=["title", "product_url"])

    df["title"] = df["title"].astype(str).str.strip()

    df["price"] = (
        df["price"]
        .astype(str)
        .str.replace("Â£", "", regex=False)
        .str.replace("£", "", regex=False)
        .str.strip()
    )

    df["price"] = pd.to_numeric(
        df["price"], errors="coerce"
    )

    df["rating"] = df["rating"].fillna("Unknown")
    df["availability"] = (
        df["availability"].fillna("Unknown")
    )

    df = df.drop_duplicates(
        subset=["product_url"], keep="last"
    )

    return df.reset_index(drop=True)


if __name__ == "__main__":
    sample_books = [
        {
            "title": " Test Book ",
            "price": "Â£19.99",
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

    cleaned = clean_books(sample_books)

    print("Original records:", len(sample_books))
    print("Cleaned records:", len(cleaned))
    print(cleaned.to_string(index=False))
