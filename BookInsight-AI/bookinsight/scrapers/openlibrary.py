"""
Open Library Scraper
Scrapes book data from Open Library (openlibrary.org).
"""

import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

from bookinsight.scrapers.base import APIScraper, ScrapedData
from bookinsight.models import Book, Author, BookFormat
from bookinsight.config import config

logger = logging.getLogger(__name__)


class OpenLibraryScraper(APIScraper):
    """Scraper for Open Library API."""
    
    def __init__(self):
        settings = config.settings.openlibrary
        super().__init__(
            name="openlibrary",
            base_url=settings.base_url,
            rate_limit=config.settings.scrapers.rate_limit,
            timeout=config.settings.scrapers.timeout,
        )
        self.covers_base_url = settings.covers_base_url
    
    async def search_books(
        self,
        query: str,
        max_results: int = 20,
        page: int = 1,
        mode: str = "everything"
    ) -> List[ScrapedData[Book]]:
        """
        Search for books using Open Library Search API.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            page: Page number for pagination
            mode: Search mode (everything, title, author, subject, isbn)
            
        Returns:
            List of ScrapedData containing Book objects
        """
        params = {
            'q': query,
            'limit': min(max_results, 100),
            'page': page,
            'mode': mode,
            'fields': 'key,title,subtitle,author_name,author_key,isbn,publisher,publish_date,'
                      'number_of_pages_median,language,subject,cover_i,cover_edition_key,'
                      'first_publish_year,edition_count,rating_average,rating_count,ia',
        }
        
        url = f"{self.base_url}/search.json"
        response = await self.get_json(url, params=params)
        
        books = []
        docs = response.get('docs', [])
        
        for doc in docs:
            try:
                book = self._parse_search_result(doc)
                if book:
                    scraped = ScrapedData(
                        data=book,
                        source_url=f"{self.base_url}{doc.get('key', '')}",
                        scraped_at=0,
                        scraper_name=self.name,
                        metadata={'openlibrary_key': doc.get('key', '')}
                    )
                    books.append(scraped)
            except Exception as e:
                logger.warning(f"Failed to parse Open Library search result: {e}")
                continue
        
        logger.info(f"Open Library search for '{query}' returned {len(books)} books")
        return books
    
    async def get_book_by_olid(self, olid: str) -> Optional[ScrapedData[Book]]:
        """Get a book by Open Library ID (OLID)."""
        # Remove OL prefix if present
        olid = olid.replace('OL', '').replace('M', '')
        url = f"{self.base_url}/works/OL{olid}W.json"
        
        try:
            response = await self.get_json(url)
            book = self._parse_work(response)
            if book:
                return ScrapedData(
                    data=book,
                    source_url=url,
                    scraped_at=0,
                    scraper_name=self.name,
                    metadata={'openlibrary_olid': olid}
                )
        except Exception as e:
            logger.error(f"Failed to get book by OLID {olid}: {e}")
        
        return None
    
    async def get_book_by_isbn(self, isbn: str) -> Optional[ScrapedData[Book]]:
        """Get a book by ISBN."""
        clean_isbn = isbn.replace('-', '').replace(' ', '')
        url = f"{self.base_url}/isbn/{clean_isbn}.json"
        
        try:
            response = await self.get_json(url)
            # ISBN endpoint returns a list of works
            if isinstance(response, list) and response:
                # Get the first work
                work_key = response[0].get('key', '')
                if work_key:
                    return await self.get_book_by_key(work_key)
        except Exception as e:
            logger.error(f"Failed to get book by ISBN {isbn}: {e}")
        
        return None
    
    async def get_book_by_key(self, key: str) -> Optional[ScrapedData[Book]]:
        """Get a book by Open Library key (e.g., /works/OL123W)."""
        url = f"{self.base_url}{key}.json"
        
        try:
            response = await self.get_json(url)
            book = self._parse_work(response)
            if book:
                return ScrapedData(
                    data=book,
                    source_url=url,
                    scraped_at=0,
                    scraper_name=self.name,
                    metadata={'openlibrary_key': key}
                )
        except Exception as e:
            logger.error(f"Failed to get book by key {key}: {e}")
        
        return None
    
    async def get_author(self, author_key: str) -> Optional[Author]:
        """Get author details by author key."""
        url = f"{self.base_url}/authors/{author_key}.json"
        
        try:
            response = await self.get_json(url)
            return self._parse_author(response)
        except Exception as e:
            logger.error(f"Failed to get author {author_key}: {e}")
        
        return None
    
    def _parse_search_result(self, doc: Dict[str, Any]) -> Optional[Book]:
        """Parse a search result document into a Book object."""
        title = doc.get('title', '').strip()
        if not title:
            return None
        
        subtitle = doc.get('subtitle', '').strip()
        
        # Authors
        authors = []
        author_names = doc.get('author_name', [])
        author_keys = doc.get('author_key', [])
        for i, name in enumerate(author_names):
            author = Author(
                name=name.strip(),
                openlibrary_id=author_keys[i] if i < len(author_keys) else ""
            )
            authors.append(author)
        
        # ISBNs
        isbns = doc.get('isbn', [])
        isbn_10 = ""
        isbn_13 = ""
        for isbn in isbns:
            clean = isbn.replace('-', '').replace(' ', '')
            if len(clean) == 10 and not isbn_10:
                isbn_10 = clean
            elif len(clean) == 13 and not isbn_13:
                isbn_13 = clean
        
        # Publication info
        publish_dates = doc.get('publish_date', [])
        publication_year = doc.get('first_publish_year', 0) or 0
        publication_date = None
        if publish_dates:
            # Use the earliest date
            try:
                dates = sorted([d for d in publish_dates if d.isdigit() and len(d) == 4])
                if dates:
                    publication_year = int(dates[0])
            except (ValueError, TypeError):
                pass
        
        # Page count
        page_count = doc.get('number_of_pages_median', 0) or 0
        
        # Language
        languages = doc.get('language', [])
        language = languages[0] if languages else 'en'
        
        # Subjects
        subjects = doc.get('subject', [])
        
        # Cover
        cover_id = doc.get('cover_i')
        cover_edition_key = doc.get('cover_edition_key')
        cover_url = ""
        cover_thumbnail_url = ""
        if cover_id:
            cover_url = f"{self.covers_base_url}/b/id/{cover_id}-L.jpg"
            cover_thumbnail_url = f"{self.covers_base_url}/b/id/{cover_id}-S.jpg"
        elif cover_edition_key:
            cover_url = f"{self.covers_base_url}/b/olid/{cover_edition_key}-L.jpg"
            cover_thumbnail_url = f"{self.covers_base_url}/b/olid/{cover_edition_key}-S.jpg"
        
        # Ratings
        average_rating = doc.get('rating_average', 0.0) or 0.0
        ratings_count = doc.get('rating_count', 0) or 0
        
        # Format
        format_type = BookFormat.PAPERBACK
        
        # Create book
        book = Book(
            title=title,
            subtitle=subtitle,
            authors=authors,
            author_names=[a.name for a in authors],
            isbn_10=isbn_10,
            isbn_13=isbn_13,
            publisher=", ".join(doc.get('publisher', [])) if doc.get('publisher') else "",
            publication_year=publication_year,
            page_count=page_count,
            format=format_type,
            language=language,
            subjects=subjects,
            cover_url=cover_url,
            cover_thumbnail_url=cover_thumbnail_url,
            openlibrary_id=doc.get('key', '').replace('/works/', '').replace('OL', '').replace('W', ''),
            average_rating=average_rating,
            ratings_count=ratings_count,
            source="openlibrary",
            source_url=f"{self.base_url}{doc.get('key', '')}",
        )
        
        return book
    
    def _parse_work(self, work: Dict[str, Any]) -> Optional[Book]:
        """Parse a work object into a Book object."""
        title = work.get('title', '').strip()
        if not title:
            return None
        
        subtitle = work.get('subtitle', '').strip()
        
        # Description
        description = ""
        desc_obj = work.get('description')
        if isinstance(desc_obj, dict):
            description = desc_obj.get('value', '').strip()
        elif isinstance(desc_obj, str):
            description = desc_obj.strip()
        
        # Authors
        authors = []
        author_refs = work.get('authors', [])
        for author_ref in author_refs:
            author_key = author_ref.get('author', {}).get('key', '')
            if author_key:
                # We could fetch author details, but for now just use the key
                author = Author(
                    name=author_ref.get('author', {}).get('name', ''),
                    openlibrary_id=author_key.replace('/authors/', '').replace('OL', '').replace('A', '')
                )
                authors.append(author)
        
        # ISBNs - need to fetch edition data for this
        isbn_10 = ""
        isbn_13 = ""
        
        # Publication info
        publication_year = work.get('first_publish_date', 0) or 0
        if isinstance(publication_year, str):
            try:
                publication_year = int(publication_year[:4])
            except (ValueError, TypeError):
                publication_year = 0
        
        # Subjects
        subjects = work.get('subjects', [])
        
        # Cover
        cover_id = work.get('cover_id')
        cover_url = ""
        cover_thumbnail_url = ""
        if cover_id:
            cover_url = f"{self.covers_base_url}/b/id/{cover_id}-L.jpg"
            cover_thumbnail_url = f"{self.covers_base_url}/b/id/{cover_id}-S.jpg"
        
        # Create book
        book = Book(
            title=title,
            subtitle=subtitle,
            authors=authors,
            author_names=[a.name for a in authors],
            isbn_10=isbn_10,
            isbn_13=isbn_13,
            description=description,
            publication_year=publication_year,
            subjects=subjects,
            cover_url=cover_url,
            cover_thumbnail_url=cover_thumbnail_url,
            openlibrary_id=work.get('key', '').replace('/works/', '').replace('OL', '').replace('W', ''),
            source="openlibrary",
            source_url=f"{self.base_url}{work.get('key', '')}",
        )
        
        return book
    
    def _parse_author(self, data: Dict[str, Any]) -> Author:
        """Parse author data into Author object."""
        name = data.get('name', '').strip()
        bio = ""
        bio_obj = data.get('bio')
        if isinstance(bio_obj, dict):
            bio = bio_obj.get('value', '').strip()
        elif isinstance(bio_obj, str):
            bio = bio_obj.strip()
        
        # Parse dates
        birth_date = None
        death_date = None
        if data.get('birth_date'):
            try:
                birth_date = datetime.fromisoformat(data['birth_date'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass
        if data.get('death_date'):
            try:
                death_date = datetime.fromisoformat(data['death_date'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass
        
        return Author(
            name=name,
            bio=bio,
            birth_date=birth_date,
            death_date=death_date,
            openlibrary_id=data.get('key', '').replace('/authors/', '').replace('OL', '').replace('A', ''),
            photo_url=f"{self.covers_base_url}/a/olid/{data.get('key', '').replace('/authors/', '').replace('OL', '').replace('A', '')}-M.jpg" if data.get('key') else "",
        )
    
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