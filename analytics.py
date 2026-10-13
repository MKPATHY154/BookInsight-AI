
import sqlite3
import pandas as pd

from config import DATABASE_PATH


def load_books():
    connection = sqlite3.connect(DATABASE_PATH)

    query = """
        SELECT title, price, rating, availability, product_url
        FROM books
    """

    df = pd.read_sql_query(query, connection)
    connection.close()

    return df


def get_summary():
    df = load_books()

    if df.empty:
        return {
            "total_books": 0,
            "average_price": 0,
            "minimum_price": 0,
            "maximum_price": 0
        }

    return {
        "total_books": len(df),
        "average_price": round(df["price"].mean(), 2),
        "minimum_price": round(df["price"].min(), 2),
        "maximum_price": round(df["price"].max(), 2)
    }


def get_top_rated_books():
    df = load_books()

    rating_order = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }

    df["rating_score"] = df["rating"].map(rating_order).fillna(0)

    return df.sort_values(
        by=["rating_score", "title"],
        ascending=[False, True]
    ).head(10)


if __name__ == "__main__":
    summary = get_summary()

    print("BOOK ANALYTICS SUMMARY")
    print("----------------------")
    print("Total books:", summary["total_books"])
    print("Average price: £", summary["average_price"])
    print("Minimum price: £", summary["minimum_price"])
    print("Maximum price: £", summary["maximum_price"])

    print("\nTOP 10 HIGHEST-RATED BOOKS")
    print(get_top_rated_books()[["title", "price", "rating"]].to_string(index=False))

def load_open_library_books():
    import sqlite3
    import pandas as pd
    from config import DATABASE_PATH

    connection = sqlite3.connect(DATABASE_PATH)

    query = """
        SELECT
            open_library_id,
            title,
            author,
            publication_year,
            isbn,
            cover_id
        FROM open_library_books
    """

    df = pd.read_sql_query(query, connection)
    connection.close()

    return df
