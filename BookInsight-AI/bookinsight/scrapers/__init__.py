"""
Scrapers Package
Exports all available scrapers and provides a factory for creating them.
"""

from bookinsight.scrapers.base import BaseScraper, HTMLScraper, APIScraper, ScrapedData, RateLimiter
from bookinsight.scrapers.google_books import GoogleBooksScraper
from bookinsight.scrapers.openlibrary import OpenLibraryScraper
from bookinsight.scrapers.goodreads import GoodreadsScraper

__all__ = [
    'BaseScraper',
    'HTMLScraper',
    'APIScraper',
    'ScrapedData',
    'RateLimiter',
    'GoogleBooksScraper',
    'OpenLibraryScraper',
    'GoodreadsScraper',
    'get_scraper',
    'list_scrapers',
]


def get_scraper(name: str, **kwargs):
    """
    Factory function to get a scraper instance by name.
    
    Args:
        name: Scraper name ('google_books', 'openlibrary', 'goodreads')
        **kwargs: Additional arguments passed to scraper constructor
        
    Returns:
        Scraper instance
        
    Raises:
        ValueError: If scraper name is unknown
    """
    scrapers = {
        'google_books': GoogleBooksScraper,
        'openlibrary': OpenLibraryScraper,
        'goodreads': GoodreadsScraper,
    }
    
    if name not in scrapers:
        raise ValueError(f"Unknown scraper: {name}. Available: {list(scrapers.keys())}")
    
    return scrapers[name](**kwargs)


def list_scrapers() -> dict:
    """Get a dictionary of available scrapers with their descriptions."""
    return {
        'google_books': {
            'class': GoogleBooksScraper,
            'description': 'Google Books API - requires API key for higher limits',
            'requires_api_key': True,
            'rate_limited': True,
        },
        'openlibrary': {
            'class': OpenLibraryScraper,
            'description': 'Open Library - free, no API key required',
            'requires_api_key': False,
            'rate_limited': True,
        },
        'goodreads': {
            'class': GoodreadsScraper,
            'description': 'Goodreads HTML scraping - use responsibly',
            'requires_api_key': False,
            'rate_limited': True,
        },
    }