
import io

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics import load_books, load_open_library_books
from config import DEFAULT_CURRENCY, SUPPORTED_CURRENCIES
from currency_converter import get_exchange_rates, convert_price
from database import save_books
from scraper import scrape_books


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="BookInsight AI",
    page_icon="📚",
    layout="wide"
)

st.title("📚 BookInsight AI")
st.caption("Advanced Book Scraping & Analytics Dashboard")


# --------------------------------------------------
# SCRAPE ORIGINAL BOOKS
# --------------------------------------------------

if st.button("🔄 Scrape Books"):
    with st.spinner("Scraping book data..."):
        books = scrape_books()

        if books:
            save_books(books)
            st.success(
                "Scraping completed! Books collected: "
                + str(len(books))
            )
            st.rerun()
        else:
            st.warning("No books were collected.")


# --------------------------------------------------
# SELECT CATALOG
# --------------------------------------------------

catalog_choice = st.sidebar.selectbox(
    "Choose Book Catalog",
    [
        "Books to Scrape",
        "Open Library"
    ]
)

is_original_catalog = catalog_choice == "Books to Scrape"


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

if is_original_catalog:
    df = load_books()
else:
    df = load_open_library_books()


if df.empty:
    st.warning("No books found in this catalog.")
    st.stop()


# --------------------------------------------------
# CURRENCY CONVERSION
# Only applies to the original catalog
# --------------------------------------------------

currency_symbol = ""

if is_original_catalog:
    st.sidebar.header("Currency Settings")

    currency_options = list(SUPPORTED_CURRENCIES.keys())

    selected_currency = st.sidebar.selectbox(
        "Choose your currency",
        currency_options,
        index=currency_options.index(DEFAULT_CURRENCY),
        format_func=lambda code: (
            code + " - " + SUPPORTED_CURRENCIES[code]["name"]
        )
    )

    rates = get_exchange_rates()

    if rates:
        df["price"] = df["price"].apply(
            lambda amount: (
                convert_price(
                    float(amount),
                    "GBP",
                    selected_currency,
                    rates
                )
                if pd.notna(amount)
                else None
            )
        )

        currency_symbol = SUPPORTED_CURRENCIES[
            selected_currency
        ]["symbol"]

    else:
        st.sidebar.warning(
            "Exchange rates unavailable. Showing prices in GBP."
        )

        selected_currency = "GBP"
        currency_symbol = "£"

    currency_label = selected_currency

else:
    currency_label = "Not available"


# --------------------------------------------------
# SUMMARY METRICS
# --------------------------------------------------

st.subheader("📊 Catalog Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Books",
    "{:,}".format(len(df))
)

if is_original_catalog:
    prices = pd.to_numeric(df["price"], errors="coerce").dropna()

    if not prices.empty:
        col2.metric(
            "Average Price",
            currency_symbol + "{:.2f}".format(prices.mean())
        )

        col3.metric(
            "Lowest Price",
            currency_symbol + "{:.2f}".format(prices.min())
        )

        col4.metric(
            "Highest Price",
            currency_symbol + "{:.2f}".format(prices.max())
        )
    else:
        col2.metric("Average Price", "N/A")
        col3.metric("Lowest Price", "N/A")
        col4.metric("Highest Price", "N/A")

else:
    col2.metric("Authors", "{:,}".format(
        df["author"].dropna().nunique()
    ))

    if "publication_year" in df.columns:
        years = pd.to_numeric(
            df["publication_year"], errors="coerce"
        ).dropna()

        col3.metric(
            "Publication Years",
            "{:,}".format(years.nunique())
        )
    else:
        col3.metric("Publication Years", "N/A")

    if "isbn" in df.columns:
        col4.metric(
            "Books with ISBN",
            "{:,}".format(df["isbn"].notna().sum())
        )
    else:
        col4.metric("Books with ISBN", "N/A")


st.divider()


# --------------------------------------------------
# SEARCH AND FILTER
# --------------------------------------------------

st.subheader("🔎 Search and Filter")

search = st.text_input("Search by book title")

if is_original_catalog:
    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        rating_options = [
            "All", "One", "Two", "Three", "Four", "Five"
        ]

        selected_rating = st.selectbox(
            "Filter by rating",
            rating_options
        )

    with filter_col2:
        availability_options = ["All"] + sorted(
            df["availability"].dropna().unique().tolist()
        )

        selected_availability = st.selectbox(
            "Filter by availability",
            availability_options
        )

    min_price = float(df["price"].min())
    max_price = float(df["price"].max())

    if min_price < max_price:
        price_range = st.slider(
            "Filter by price (" + currency_label + ")",
            min_value=min_price,
            max_value=max_price,
            value=(min_price, max_price)
        )
    else:
        price_range = (min_price, max_price)

    sort_options = [
        "Highest Rating",
        "Best Value",
        "Lowest Rating",
        "Lowest Price",
        "Highest Price",
        "Title (A–Z)",
        "Title (Z–A)"
    ]

else:
    selected_rating = "All"
    selected_availability = "All"
    price_range = None

    sort_options = [
        "Title (A–Z)",
        "Title (Z–A)",
        "Newest Publication",
        "Oldest Publication",
        "Author (A–Z)"
    ]


sort_option = st.selectbox(
    "Sort books by",
    sort_options
)


# --------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------

filtered_df = df.copy()

if search:
    filtered_df = filtered_df[
        filtered_df["title"].str.contains(
            search,
            case=False,
            na=False
        )
    ]

if is_original_catalog:
    if selected_rating != "All":
        filtered_df = filtered_df[
            filtered_df["rating"] == selected_rating
        ]

    if selected_availability != "All":
        filtered_df = filtered_df[
            filtered_df["availability"] == selected_availability
        ]

    filtered_df = filtered_df[
        (filtered_df["price"] >= price_range[0])
        & (filtered_df["price"] <= price_range[1])
    ]


# --------------------------------------------------
# SORT BOOKS
# --------------------------------------------------

if is_original_catalog:
    rating_order = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }

    filtered_df["rating_score"] = (
        filtered_df["rating"].map(rating_order).fillna(0)
    )

    if sort_option == "Highest Rating":
        filtered_df = filtered_df.sort_values(
            "rating_score", ascending=False
        )

    elif sort_option == "Lowest Rating":
        filtered_df = filtered_df.sort_values(
            "rating_score", ascending=True
        )

    elif sort_option == "Best Value":
        filtered_df["value_score"] = (
            filtered_df["rating_score"]
            / filtered_df["price"].replace(0, float("nan"))
        )

        filtered_df = filtered_df.sort_values(
            "value_score", ascending=False, na_position="last"
        )

        filtered_df = filtered_df.drop(
            columns=["value_score"]
        )

    elif sort_option == "Lowest Price":
        filtered_df = filtered_df.sort_values(
            "price", ascending=True, na_position="last"
        )

    elif sort_option == "Highest Price":
        filtered_df = filtered_df.sort_values(
            "price", ascending=False, na_position="last"
        )

    elif sort_option == "Title (A–Z)":
        filtered_df = filtered_df.sort_values(
            "title", ascending=True
        )

    elif sort_option == "Title (Z–A)":
        filtered_df = filtered_df.sort_values(
            "title", ascending=False
        )

    filtered_df = filtered_df.drop(
        columns=["rating_score"]
    )

else:
    if sort_option == "Title (A–Z)":
        filtered_df = filtered_df.sort_values(
            "title", ascending=True
        )

    elif sort_option == "Title (Z–A)":
        filtered_df = filtered_df.sort_values(
            "title", ascending=False
        )

    elif sort_option == "Author (A–Z)":
        filtered_df = filtered_df.sort_values(
            "author", ascending=True, na_position="last"
        )

    elif sort_option == "Newest Publication":
        filtered_df = filtered_df.sort_values(
            "publication_year", ascending=False,
            na_position="last"
        )

    elif sort_option == "Oldest Publication":
        filtered_df = filtered_df.sort_values(
            "publication_year", ascending=True,
            na_position="last"
        )


# --------------------------------------------------
# DISPLAY BOOK CATALOG
# --------------------------------------------------

st.subheader("📖 Book Catalog")

st.caption(
    "Showing {:,} books from {}.".format(
        len(filtered_df), catalog_choice
    )
)

if is_original_catalog:
    rating_stars = {
        "One": "⭐☆☆☆☆",
        "Two": "⭐⭐☆☆☆",
        "Three": "⭐⭐⭐☆☆",
        "Four": "⭐⭐⭐⭐☆",
        "Five": "⭐⭐⭐⭐⭐"
    }

    display_df = filtered_df.copy()

    display_df["rating"] = (
        display_df["rating"]
        .map(rating_stars)
        .fillna("☆☆☆☆☆")
    )

else:
    display_columns = [
        "title",
        "author",
        "publication_year",
        "isbn",
        "cover_id"
    ]

    display_df = filtered_df[
        [
            column for column in display_columns
            if column in filtered_df.columns
        ]
    ].copy()

st.dataframe(
    display_df,
    width="stretch",
    hide_index=True
)


# --------------------------------------------------
# EXPORT CSV AND EXCEL
# --------------------------------------------------

csv_data = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇️ Download CSV",
    data=csv_data,
    file_name=(
        "books_" + currency_label.lower() + ".csv"
        if is_original_catalog
        else "open_library_books.csv"
    ),
    mime="text/csv",
    width="stretch"
)

excel_buffer = io.BytesIO()

with pd.ExcelWriter(
    excel_buffer,
    engine="openpyxl"
) as writer:
    filtered_df.to_excel(
        writer,
        index=False,
        sheet_name="Books"
    )

st.download_button(
    "📊 Download Excel",
    data=excel_buffer.getvalue(),
    file_name=(
        "books_" + currency_label.lower() + ".xlsx"
        if is_original_catalog
        else "open_library_books.xlsx"
    ),
    mime=(
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    ),
    width="stretch"
)


# --------------------------------------------------
# ANALYTICS
# --------------------------------------------------

st.divider()
st.subheader("📈 Book Analytics")

if is_original_catalog:
    st.subheader("💰 Price Analysis")

    price_chart = px.histogram(
        filtered_df.dropna(subset=["price"]),
        x="price",
        nbins=20,
        title="Distribution of Book Prices",
        labels={
            "price": "Price (" + currency_label + ")"
        }
    )

    st.plotly_chart(
        price_chart,
        use_container_width=True
    )

    st.subheader("⭐ Rating Distribution")

    rating_chart = px.bar(
        filtered_df["rating"].value_counts()
        .rename_axis("Rating")
        .reset_index(name="Number of Books"),
        x="Rating",
        y="Number of Books",
        title="Books by Rating"
    )

    st.plotly_chart(
        rating_chart,
        use_container_width=True
    )

else:
    if "publication_year" in filtered_df.columns:
        year_data = filtered_df.copy()

        year_data["publication_year"] = pd.to_numeric(
            year_data["publication_year"],
            errors="coerce"
        )

        year_data = year_data.dropna(
            subset=["publication_year"]
        )

        if not year_data.empty:
            year_chart = px.histogram(
                year_data,
                x="publication_year",
                nbins=30,
                title="Distribution of Publication Years",
                labels={
                    "publication_year": "First Publication Year"
                }
            )

            st.plotly_chart(
                year_chart,
                use_container_width=True
            )
        else:
            st.info("Publication-year data is unavailable.")

    st.subheader("✍️ Top Authors")

    if "author" in filtered_df.columns:
        author_data = filtered_df[
            filtered_df["author"].notna()
            & (filtered_df["author"].str.strip() != "")
        ]

        author_counts = (
            author_data["author"]
            .value_counts()
            .head(10)
            .rename_axis("Author")
            .reset_index(name="Number of Books")
        )

        if not author_counts.empty:
            author_chart = px.bar(
                author_counts,
                x="Number of Books",
                y="Author",
                orientation="h",
                title="Top 10 Authors in the Current Catalog"
            )

            st.plotly_chart(
                author_chart,
                use_container_width=True
            )
        else:
            st.info("Author data is unavailable.")
