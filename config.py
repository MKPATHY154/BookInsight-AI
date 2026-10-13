BASE_URL = "https://books.toscrape.com/"
REQUEST_TIMEOUT = 15
REQUEST_DELAY = 1
MAX_PAGES = 50

DATABASE_PATH = "data/books.db"
EXPORT_FOLDER = "exports"
DEFAULT_CURRENCY = "INR"

SUPPORTED_CURRENCIES = {
    "INR": {"name": "Indian Rupee", "symbol": "₹"},
    "USD": {"name": "US Dollar", "symbol": "$"},
    "GBP": {"name": "British Pound", "symbol": "£"},
    "EUR": {"name": "Euro", "symbol": "€"},
    "AUD": {"name": "Australian Dollar", "symbol": "A$"},
    "CAD": {"name": "Canadian Dollar", "symbol": "C$"},
    "JPY": {"name": "Japanese Yen", "symbol": "¥"},
    "SGD": {"name": "Singapore Dollar", "symbol": "S$"},
    "AED": {"name": "UAE Dirham", "symbol": "د.إ"},
}