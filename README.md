# BookInsight AI 📚

BookInsight AI is a Python-based book analytics dashboard that collects, stores, analyzes, and displays book information through an interactive web interface.

## Features

- **Book Data Collection:** Scrape book information from Books to Scrape.
- **Open Library Integration:** Collect book metadata from Open Library.
- **Interactive Dashboard:** Explore book data using Streamlit.
- **Data Analytics:** View summaries and visualizations of book information.
- **Search and Filtering:** Find books based on available details.
- **Currency Support:** Display supported currency options for book prices.
- **Data Export:** Export available results to CSV or Excel, where supported.
- **SQLite Database:** Store book records locally.
- **Automated Tests:** Test database and data-cleaning functionality.

## Technologies Used

- Python
- Streamlit
- SQLite
- Pandas
- Plotly
- Beautiful Soup
- Requests
- Open Library Search API
- Pytest

## Project Structure

```text
advance-book/
├── app.py
├── scraper.py
├── open_library.py
├── database.py
├── analytics.py
├── data_cleaner.py
├── currency_converter.py
├── config.py
├── requirements.txt
├── README.md
├── data/
│   └── books.db
└── tests/
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/MKPATHY154/BookInsight-AI.git
cd BookInsight-AI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment on Windows

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

## Run the Application

Start the Streamlit dashboard:

```bash
python -m streamlit run app.py
```

Open the local URL shown in your terminal, usually `http://localhost:8501`.

## Database

The project uses SQLite to store book records. The database is located at `data/books.db`.

## Testing

Run the automated tests with:

```bash
python -m pytest
```

## Future Improvements

- Improve book metadata coverage.
- Add more advanced analytics and filtering.
- Improve data validation and error handling.
- Deploy the dashboard online.
- Add more book data sources.

## Author

**Manoj Kumar Pathy**

GitHub: [MKPATHY154](https://github.com/MKPATHY154)

## License

No license has been specified yet. Contact the repository owner before reusing this project.
