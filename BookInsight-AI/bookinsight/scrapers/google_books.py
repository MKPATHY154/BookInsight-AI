"""
Google Books API Scraper
Scrapes book data from Google Books API.
"""

import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

from bookinsight.scrapers.base import APIScraper, ScrapedData
from bookinsight.models import Book, Author, BookFormat
from bookinsight.config import config

logger = logging.getLogger(__name__)


class GoogleBooksScraper(APIScraper):
    """Scraper for Google Books API."""
    
    def __init__(self, api_key: Optional[str] = None):
        settings = config.settings.google_books
        super().__init__(
            name="google_books",
            base_url=settings.base_url,
            rate_limit=config.settings.scrapers.rate_limit,
            timeout=config.settings.scrapers.timeout,
        )
        self.api_key = api_key or settings.api_key
        self.max_results = settings.max_results
    
    async def search_books(
        self,
        query: str,
        max_results: Optional[int] = None,
        start_index: int = 0,
        lang_restrict: str = "en",
        print_type: str = "books",
        order_by: str = "relevance"
    ) -> List[ScrapedData[Book]]:
        """
        Search for books using Google Books API.
        
        Args:
            query: Search query (title, author, ISBN, etc.)
            max_results: Maximum results to return (default from config)
            start_index: Starting index for pagination
            lang_restrict: Language restriction (ISO 639-1 code)
            print_type: Type of books (books, magazines)
            order_by: Sort order (relevance, newest)
            
        Returns:
            List of ScrapedData containing Book objects
        """
        params = {
            'q': query,
            'maxResults': max_results or self.max_results,
            'startIndex': start_index,
            'langRestrict': lang_restrict,
            'printType': print_type,
            'orderBy': order_by,
        }
        
        if self.api_key:
            params['key'] = self.api_key
        
        url = f"{self.base_url}/volumes"
        response = await self.get_json(url, params=params)
        
        books = []
        items = response.get('items', [])
        
        for item in items:
            try:
                book = self._parse_volume(item)
                if book:
                    scraped = ScrapedData(
                        data=book,
                        source_url=f"{self.base_url}/volumes/{item.get('id', '')}",
                        scraped_at=0,  # Will be set by base class
                        scraper_name=self.name,
                        metadata={'google_books_id': item.get('id', '')}
                    )
                    books.append(scraped)
            except Exception as e:
                logger.warning(f"Failed to parse Google Books item: {e}")
                continue
        
        logger.info(f"Google Books search for '{query}' returned {len(books)} books")
        return books
    
    async def get_book_by_id(self, volume_id: str) -> Optional[ScrapedData[Book]]:
        """Get a single book by Google Books volume ID."""
        url = f"{self.base_url}/volumes/{volume_id}"
        params = {}
        if self.api_key:
            params['key'] = self.api_key
        
        try:
            response = await self.get_json(url, params=params)
            book = self._parse_volume(response)
            if book:
                return ScrapedData(
                    data=book,
                    source_url=url,
                    scraped_at=0,
                    scraper_name=self.name,
                    metadata={'google_books_id': volume_id}
                )
        except Exception as e:
            logger.error(f"Failed to get book by ID {volume_id}: {e}")
        
        return None
    
    async def get_book_by_isbn(self, isbn: str) -> Optional[ScrapedData[Book]]:
        """Get a book by ISBN."""
        # Clean ISBN
        clean_isbn = isbn.replace('-', '').replace(' ', '')
        query = f"isbn:{clean_isbn}"
        results = await self.search_books(query, max_results=1)
        return results[0] if results else None
    
    def _parse_volume(self, volume: Dict[str, Any]) -> Optional[Book]:
        """Parse a Google Books volume into a Book object."""
        volume_info = volume.get('volumeInfo', {})
        if not volume_info:
            return None
        
        # Extract basic info
        title = volume_info.get('title', '').strip()
        if not title:
            return None
        
        subtitle = volume_info.get('subtitle', '').strip()
        
        # Authors
        authors = []
        author_names = volume_info.get('authors', [])
        for author_name in author_names:
            author = Author(name=author_name.strip())
            authors.append(author)
        
        # ISBNs
        isbn_10 = ""
        isbn_13 = ""
        for identifier in volume_info.get('industryIdentifiers', []):
            if identifier.get('type') == 'ISBN_10':
                isbn_10 = identifier.get('identifier', '')
            elif identifier.get('type') == 'ISBN_13':
                isbn_13 = identifier.get('identifier', '')
        
        # Publication info
        published_date = volume_info.get('publishedDate', '')
        publication_year = 0
        publication_date = None
        if published_date:
            # Parse date (can be YYYY, YYYY-MM, or YYYY-MM-DD)
            parts = published_date.split('-')
            try:
                publication_year = int(parts[0])
                if len(parts) >= 3:
                    publication_date = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                elif len(parts) == 2:
                    publication_date = datetime(int(parts[0]), int(parts[1]), 1)
            except (ValueError, IndexError):
                pass
        
        # Description
        description = volume_info.get('description', '').strip()
        
        # Page count
        page_count = volume_info.get('pageCount', 0) or 0
        
        # Format
        print_type = volume_info.get('printType', 'BOOK').lower()
        if print_type == 'book':
            format_type = BookFormat.PAPERBACK
        elif print_type == 'magazine':
            format_type = BookFormat.OTHER
        else:
            format_type = BookFormat.OTHER
        
        # Language
        language = volume_info.get('language', 'en')
        
        # Categories/Subjects
        subjects = volume_info.get('categories', [])
        
        # Cover images
        image_links = volume_info.get('imageLinks', {})
        cover_url = image_links.get('large') or image_links.get('medium') or image_links.get('thumbnail', '')
        cover_thumbnail_url = image_links.get('thumbnail', '')
        
        # Ratings
        average_rating = volume_info.get('averageRating', 0.0) or 0.0
        ratings_count = volume_info.get('ratingsCount', 0) or 0
        
        # Create book
        book = Book(
            title=title,
            subtitle=subtitle,
            authors=authors,
            author_names=[a.name for a in authors],
            isbn_10=isbn_10,
            isbn_13=isbn_13,
            publisher=volume_info.get('publisher', '').strip(),
            publication_date=publication_date,
            publication_year=publication_year,
            description=description,
            page_count=page_count,
            format=format_type,
            language=language,
            subjects=subjects,
            cover_url=cover_url,
            cover_thumbnail_url=cover_thumbnail_url,
            google_books_id=volume.get('id', ''),
            average_rating=average_rating,
            ratings_count=ratings_count,
            source="google_books",
            source_url=f"{self.base_url}/volumes/{volume.get('id', '')}",
        )
        
        return book
    
    async def scrape(self, query: str, **kwargs) -> List[ScrapedData[Book]]:
        """
        Main scrape method - searches for books by query.
        
        Args:
            query: Search query
            **kwargs: Additional arguments passed to search_books
            
        Returns:
            List of ScrapedData containing Book objects
        """
        return await self.search_books(query, **kwargs)


# Import datetime for parsing
from datetime import datetime