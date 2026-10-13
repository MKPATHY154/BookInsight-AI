"""
Goodreads Scraper
Scrapes book data from Goodreads using HTML parsing.
Note: Goodreads has anti-scraping measures. Use responsibly and consider using their official API if available.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus, urljoin

from bookinsight.scrapers.base import HTMLScraper, ScrapedData
from bookinsight.models import Book, Author, BookFormat, BookStatus
from bookinsight.config import config

logger = logging.getLogger(__name__)


class GoodreadsScraper(HTMLScraper):
    """Scraper for Goodreads website."""
    
    def __init__(self):
        settings = config.settings.goodreads
        super().__init__(
            name="goodreads",
            base_url=settings.base_url,
            rate_limit=config.settings.scrapers.rate_limit,
            timeout=config.settings.scrapers.timeout,
        )
        self.enabled = settings.enabled
    
    async def search_books(
        self,
        query: str,
        max_results: int = 20,
        page: int = 1
    ) -> List[ScrapedData[Book]]:
        """
        Search for books on Goodreads.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            page: Page number for pagination
            
        Returns:
            List of ScrapedData containing Book objects
        """
        if not self.enabled:
            logger.warning("Goodreads scraper is disabled in config")
            return []
        
        params = {
            'q': query,
            'page': page,
        }
        
        url = f"{self.base_url}/search"
        soup = await self.get_soup(url, params=params)
        
        books = []
        # Find book results in the search page
        book_elements = soup.select('table.tableList tr')
        
        for elem in book_elements[:max_results]:
            try:
                book = self._parse_search_result(elem)
                if book:
                    scraped = ScrapedData(
                        data=book,
                        source_url=url,
                        scraped_at=0,
                        scraper_name=self.name,
                        metadata={'search_query': query}
                    )
                    books.append(scraped)
            except Exception as e:
                logger.warning(f"Failed to parse Goodreads search result: {e}")
                continue
        
        logger.info(f"Goodreads search for '{query}' returned {len(books)} books")
        return books
    
    async def get_book_by_id(self, book_id: str) -> Optional[ScrapedData[Book]]:
        """Get a book by Goodreads book ID."""
        if not self.enabled:
            return None
        
        url = f"{self.base_url}/book/show/{book_id}"
        soup = await self.get_soup(url)
        
        try:
            book = self._parse_book_page(soup, book_id)
            if book:
                return ScrapedData(
                    data=book,
                    source_url=url,
                    scraped_at=0,
                    scraper_name=self.name,
                    metadata={'goodreads_id': book_id}
                )
        except Exception as e:
            logger.error(f"Failed to get book by ID {book_id}: {e}")
        
        return None
    
    async def get_book_by_isbn(self, isbn: str) -> Optional[ScrapedData[Book]]:
        """Get a book by ISBN."""
        if not self.enabled:
            return None
        
        clean_isbn = isbn.replace('-', '').replace(' ', '')
        url = f"{self.base_url}/search"
        params = {'q': clean_isbn}
        
        soup = await self.get_soup(url, params=params)
        
        # Find first result link
        first_result = soup.select_one('table.tableList tr td.width100 a.bookTitle')
        if first_result and first_result.get('href'):
            book_url = urljoin(self.base_url, first_result['href'])
            # Extract book ID from URL
            match = re.search(r'/book/show/(\d+)', book_url)
            if match:
                return await self.get_book_by_id(match.group(1))
        
        return None
    
    async def get_reviews(
        self,
        book_id: str,
        max_reviews: int = 50
    ) -> List[Dict[str, Any]]:
        """Get reviews for a book."""
        if not self.enabled:
            return []
        
        url = f"{self.base_url}/book/show/{book_id}/reviews"
        params = {'page': 1}
        soup = await self.get_soup(url, params=params)
        
        reviews = []
        review_elements = soup.select('div.review')
        
        for elem in review_elements[:max_reviews]:
            try:
                review = self._parse_review(elem)
                if review:
                    reviews.append(review)
            except Exception as e:
                logger.warning(f"Failed to parse review: {e}")
                continue
        
        return reviews
    
    def _parse_search_result(self, elem) -> Optional[Book]:
        """Parse a search result row into a Book object."""
        # Title and link
        title_elem = elem.select_one('a.bookTitle')
        if not title_elem:
            return None
        
        title = title_elem.get_text(strip=True)
        book_url = urljoin(self.base_url, title_elem.get('href', ''))
        
        # Extract book ID from URL
        book_id_match = re.search(r'/book/show/(\d+)', book_url)
        book_id = book_id_match.group(1) if book_id_match else ""
        
        # Author
        author_elem = elem.select_one('a.authorName')
        author_name = author_elem.get_text(strip=True) if author_elem else ""
        author_url = urljoin(self.base_url, author_elem.get('href', '')) if author_elem else ""
        
        # Rating
        rating_elem = elem.select_one('span.minirating')
        average_rating = 0.0
        ratings_count = 0
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            # Parse "4.23 avg rating — 1,234,567 ratings"
            match = re.search(r'([\d.]+)\s+avg rating\s*[—-]\s*([\d,]+)\s*ratings?', rating_text)
            if match:
                average_rating = float(match.group(1))
                ratings_count = int(match.group(2).replace(',', ''))
        
        # Cover image
        cover_elem = elem.select_one('img.bookCover')
        cover_url = cover_elem.get('src', '') if cover_elem else ""
        
        # Publication info
        pub_elem = elem.select_one('span.greyText.smallText')
        publisher = ""
        publication_year = 0
        if pub_elem:
            pub_text = pub_elem.get_text(strip=True)
            # Parse "Published 2001 by Publisher Name"
            match = re.search(r'Published\s+(\d{4})\s+by\s+(.+)', pub_text)
            if match:
                publication_year = int(match.group(1))
                publisher = match.group(2).strip()
        
        # Create author
        author = Author(name=author_name) if author_name else None
        
        book = Book(
            title=title,
            authors=[author] if author else [],
            author_names=[author_name] if author_name else [],
            goodreads_id=book_id,
            publisher=publisher,
            publication_year=publication_year,
            average_rating=average_rating,
            ratings_count=ratings_count,
            cover_url=cover_url,
            source="goodreads",
            source_url=book_url,
        )
        
        return book
    
    def _parse_book_page(self, soup, book_id: str) -> Optional[Book]:
        """Parse a book detail page into a Book object."""
        # Title
        title_elem = soup.select_one('h1#bookTitle, h1.Text__title1')
        title = title_elem.get_text(strip=True) if title_elem else ""
        if not title:
            return None
        
        # Subtitle
        subtitle_elem = soup.select_one('h2#bookSubtitle, h2.Text__subtitle1')
        subtitle = subtitle_elem.get_text(strip=True) if subtitle_elem else ""
        
        # Authors
        authors = []
        author_elements = soup.select('a.authorName, a.ContributorLink')
        for author_elem in author_elements:
            author_name = author_elem.get_text(strip=True)
            author_url = urljoin(self.base_url, author_elem.get('href', ''))
            author_id_match = re.search(r'/author/show/(\d+)', author_url)
            author_id = author_id_match.group(1) if author_id_match else ""
            
            author = Author(
                name=author_name,
                goodreads_id=author_id,
            )
            authors.append(author)
        
        # Description
        desc_elem = soup.select_one('div#description, div.BookPageMetadataSection__description')
        description = ""
        if desc_elem:
            # Get the full description, handling "more" links
            desc_spans = desc_elem.select('span')
            if desc_spans:
                description = desc_spans[-1].get_text(strip=True)
            else:
                description = desc_elem.get_text(strip=True)
        
        # ISBN and publication details
        isbn_10 = ""
        isbn_13 = ""
        publisher = ""
        publication_year = 0
        page_count = 0
        format_type = BookFormat.OTHER
        language = "en"
        
        # Details section
        details = soup.select('div.BookDetails div.FeaturedDetails, div#details .row')
        for detail in details:
            label_elem = detail.select_one('div.infoBoxRowTitle, div.BookDetails__label')
            value_elem = detail.select_one('div.infoBoxRowItem, div.BookDetails__value')
            
            if label_elem and value_elem:
                label = label_elem.get_text(strip=True).lower()
                value = value_elem.get_text(strip=True)
                
                if 'isbn' in label:
                    clean = value.replace('-', '').replace(' ', '')
                    if len(clean) == 10:
                        isbn_10 = clean
                    elif len(clean) == 13:
                        isbn_13 = clean
                elif 'publisher' in label:
                    publisher = value
                elif 'published' in label:
                    # Parse "January 1, 2001"
                    match = re.search(r'(\d{4})', value)
                    if match:
                        publication_year = int(match.group(1))
                elif 'pages' in label:
                    match = re.search(r'(\d+)', value)
                    if match:
                        page_count = int(match.group(1))
                elif 'format' in label:
                    format_map = {
                        'hardcover': BookFormat.HARDCOVER,
                        'paperback': BookFormat.PAPERBACK,
                        'kindle': BookFormat.KINDLE,
                        'ebook': BookFormat.EBOOK,
                        'audiobook': BookFormat.AUDIOBOOK,
                    }
                    format_type = format_map.get(value.lower(), BookFormat.OTHER)
                elif 'language' in label:
                    language = value.lower()[:2]
        
        # Genres/Subjects
        subjects = []
        genre_elements = soup.select('a.BookPageMetadataSection__genreButton, a.actionLinkLite.bookPageGenreLink')
        for genre_elem in genre_elements:
            genre = genre_elem.get_text(strip=True)
            if genre:
                subjects.append(genre)
        
        # Rating
        rating_elem = soup.select_one('span.RatingStatistics__rating, span.average')
        average_rating = 0.0
        if rating_elem:
            try:
                average_rating = float(rating_elem.get_text(strip=True))
            except ValueError:
                pass
        
        ratings_count_elem = soup.select_one('span.RatingStatistics__meta, a.gr-hyperlink[href*="ratings"]')
        ratings_count = 0
        if ratings_count_elem:
            text = ratings_count_elem.get_text(strip=True)
            match = re.search(r'([\d,]+)\s*ratings?', text)
            if match:
                ratings_count = int(match.group(1).replace(',', ''))
        
        # Cover
        cover_elem = soup.select_one('img#coverImage, img.ResponsiveImage')
        cover_url = cover_elem.get('src', '') if cover_elem else ""
        
        # Create book
        book = Book(
            title=title,
            subtitle=subtitle,
            authors=authors,
            author_names=[a.name for a in authors],
            isbn_10=isbn_10,
            isbn_13=isbn_13,
            publisher=publisher,
            publication_year=publication_year,
            description=description,
            page_count=page_count,
            format=format_type,
            language=language,
            subjects=subjects,
            cover_url=cover_url,
            goodreads_id=book_id,
            average_rating=average_rating,
            ratings_count=ratings_count,
            source="goodreads",
            source_url=f"{self.base_url}/book/show/{book_id}",
        )
        
        return book
    
    def _parse_review(self, elem) -> Optional[Dict[str, Any]]:
        """Parse a review element."""
        # Reviewer
        reviewer_elem = elem.select_one('a.user, a.ReviewerProfile__name')
        reviewer_name = reviewer_elem.get_text(strip=True) if reviewer_elem else ""
        reviewer_url = urljoin(self.base_url, reviewer_elem.get('href', '')) if reviewer_elem else ""
        
        # Rating
        rating = None
        rating_elem = elem.select_one('span.staticStars, span.RatingStars')
        if rating_elem:
            # Try to get from title attribute or class
            title = rating_elem.get('title', '')
            match = re.search(r'(\d)\s*out of\s*5', title)
            if match:
                rating = int(match.group(1))
            else:
                # Try from class like "staticStars notranslate p10"
                classes = rating_elem.get('class', [])
                for cls in classes:
                    match = re.search(r'p(\d+)', cls)
                    if match:
                        rating = int(match.group(1))
                        break
        
        # Review text
        text_elem = elem.select_one('div.reviewText, div.ReviewText__content')
        content = text_elem.get_text(strip=True) if text_elem else ""
        
        # Date
        date_elem = elem.select_one('a.reviewDate, span.ReviewDate')
        date_posted = None
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            # Parse date - format varies
            try:
                from datetime import datetime
                date_posted = datetime.strptime(date_text, '%b %d, %Y')
            except ValueError:
                pass
        
        return {
            'reviewer_name': reviewer_name,
            'reviewer_url': reviewer_url,
            'rating': rating,
            'content': content,
            'date_posted': date_posted,
        }
    
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