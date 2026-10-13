"""
Data Models for BookInsight-AI
Defines Book, Author, Review, Rating, and other core models with validation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid
import re


class BookFormat(Enum):
    """Book format types."""
    HARDCOVER = "hardcover"
    PAPERBACK = "paperback"
    EBOOK = "ebook"
    AUDIOBOOK = "audiobook"
    KINDLE = "kindle"
    OTHER = "other"


class BookStatus(Enum):
    """Book reading status."""
    WANT_TO_READ = "want_to_read"
    CURRENTLY_READING = "currently_reading"
    READ = "read"
    DID_NOT_FINISH = "did_not_finish"


@dataclass
class Author:
    """Author model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    bio: str = ""
    birth_date: Optional[datetime] = None
    death_date: Optional[datetime] = None
    website: str = ""
    photo_url: str = ""
    goodreads_id: str = ""
    openlibrary_id: str = ""
    wikipedia_url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Author name is required")
        self.name = self.name.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'bio': self.bio,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'death_date': self.death_date.isoformat() if self.death_date else None,
            'website': self.website,
            'photo_url': self.photo_url,
            'goodreads_id': self.goodreads_id,
            'openlibrary_id': self.openlibrary_id,
            'wikipedia_url': self.wikipedia_url,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Author':
        """Create Author from dictionary."""
        author = cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', ''),
            bio=data.get('bio', ''),
            website=data.get('website', ''),
            photo_url=data.get('photo_url', ''),
            goodreads_id=data.get('goodreads_id', ''),
            openlibrary_id=data.get('openlibrary_id', ''),
            wikipedia_url=data.get('wikipedia_url', ''),
            metadata=data.get('metadata', {}),
        )
        
        # Parse dates
        for date_field in ['birth_date', 'death_date', 'created_at', 'updated_at']:
            if data.get(date_field):
                try:
                    setattr(author, date_field, datetime.fromisoformat(data[date_field]))
                except (ValueError, TypeError):
                    pass
        
        return author


@dataclass
class Book:
    """Book model with comprehensive metadata."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    subtitle: str = ""
    authors: List[Author] = field(default_factory=list)
    author_names: List[str] = field(default_factory=list)  # For quick search
    isbn_10: str = ""
    isbn_13: str = ""
    isbn: str = ""  # Primary ISBN (prefer 13)
    publisher: str = ""
    publication_date: Optional[datetime] = None
    publication_year: int = 0
    description: str = ""
    page_count: int = 0
    format: BookFormat = BookFormat.OTHER
    language: str = "en"
    subjects: List[str] = field(default_factory=list)  # Genres/categories
    cover_url: str = ""
    cover_thumbnail_url: str = ""
    
    # Identifiers from different sources
    goodreads_id: str = ""
    google_books_id: str = ""
    openlibrary_id: str = ""
    librarything_id: str = ""
    asin: str = ""  # Amazon ASIN
    
    # Ratings and reviews
    average_rating: float = 0.0
    ratings_count: int = 0
    reviews_count: int = 0
    my_rating: Optional[int] = None  # 1-5 stars
    my_review: str = ""
    status: BookStatus = BookStatus.WANT_TO_READ
    date_started: Optional[datetime] = None
    date_finished: Optional[datetime] = None
    
    # Price info
    price: float = 0.0
    currency: str = "USD"
    price_url: str = ""
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""  # Which scraper/source this came from
    source_url: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.title:
            raise ValueError("Book title is required")
        self.title = self.title.strip()
        
        # Clean ISBNs
        self.isbn_10 = self._clean_isbn(self.isbn_10)
        self.isbn_13 = self._clean_isbn(self.isbn_13)
        self.isbn = self.isbn_13 or self.isbn_10
        
        # Extract author names for search
        if self.authors and not self.author_names:
            self.author_names = [a.name for a in self.authors]
        
        # Set publication year from date
        if self.publication_date and not self.publication_year:
            self.publication_year = self.publication_date.year
    
    @staticmethod
    def _clean_isbn(isbn: str) -> str:
        """Clean ISBN by removing hyphens and spaces."""
        if not isbn:
            return ""
        return re.sub(r'[-\s]', '', isbn).upper()
    
    def get_primary_author(self) -> Optional[Author]:
        """Get the first/primary author."""
        return self.authors[0] if self.authors else None
    
    def get_author_names_str(self) -> str:
        """Get author names as a formatted string."""
        return ", ".join(self.author_names) if self.author_names else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'subtitle': self.subtitle,
            'authors': [a.to_dict() for a in self.authors],
            'author_names': self.author_names,
            'isbn_10': self.isbn_10,
            'isbn_13': self.isbn_13,
            'isbn': self.isbn,
            'publisher': self.publisher,
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'publication_year': self.publication_year,
            'description': self.description,
            'page_count': self.page_count,
            'format': self.format.value,
            'language': self.language,
            'subjects': self.subjects,
            'cover_url': self.cover_url,
            'cover_thumbnail_url': self.cover_thumbnail_url,
            'goodreads_id': self.goodreads_id,
            'google_books_id': self.google_books_id,
            'openlibrary_id': self.openlibrary_id,
            'librarything_id': self.librarything_id,
            'asin': self.asin,
            'average_rating': self.average_rating,
            'ratings_count': self.ratings_count,
            'reviews_count': self.reviews_count,
            'my_rating': self.my_rating,
            'my_review': self.my_review,
            'status': self.status.value,
            'date_started': self.date_started.isoformat() if self.date_started else None,
            'date_finished': self.date_finished.isoformat() if self.date_finished else None,
            'price': self.price,
            'currency': self.currency,
            'price_url': self.price_url,
            'metadata': self.metadata,
            'source': self.source,
            'source_url': self.source_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Book':
        """Create Book from dictionary."""
        book = cls(
            id=data.get('id', str(uuid.uuid4())),
            title=data.get('title', ''),
            subtitle=data.get('subtitle', ''),
            author_names=data.get('author_names', []),
            isbn_10=data.get('isbn_10', ''),
            isbn_13=data.get('isbn_13', ''),
            publisher=data.get('publisher', ''),
            publication_year=data.get('publication_year', 0),
            description=data.get('description', ''),
            page_count=data.get('page_count', 0),
            format=BookFormat(data.get('format', 'other')),
            language=data.get('language', 'en'),
            subjects=data.get('subjects', []),
            cover_url=data.get('cover_url', ''),
            cover_thumbnail_url=data.get('cover_thumbnail_url', ''),
            goodreads_id=data.get('goodreads_id', ''),
            google_books_id=data.get('google_books_id', ''),
            openlibrary_id=data.get('openlibrary_id', ''),
            librarything_id=data.get('librarything_id', ''),
            asin=data.get('asin', ''),
            average_rating=data.get('average_rating', 0.0),
            ratings_count=data.get('ratings_count', 0),
            reviews_count=data.get('reviews_count', 0),
            my_rating=data.get('my_rating'),
            my_review=data.get('my_review', ''),
            status=BookStatus(data.get('status', 'want_to_read')),
            price=data.get('price', 0.0),
            currency=data.get('currency', 'USD'),
            price_url=data.get('price_url', ''),
            metadata=data.get('metadata', {}),
            source=data.get('source', ''),
            source_url=data.get('source_url', ''),
        )
        
        # Parse authors
        authors_data = data.get('authors', [])
        book.authors = [Author.from_dict(a) for a in authors_data]
        
        # Parse dates
        for date_field in ['publication_date', 'date_started', 'date_finished', 'created_at', 'updated_at']:
            if data.get(date_field):
                try:
                    setattr(book, date_field, datetime.fromisoformat(data[date_field]))
                except (ValueError, TypeError):
                    pass
        
        return book


@dataclass
class Review:
    """Book review model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    book_id: str = ""
    author_id: str = ""  # Reviewer ID
    author_name: str = ""
    rating: Optional[int] = None  # 1-5 stars
    title: str = ""
    content: str = ""
    source: str = ""  # goodreads, google_books, etc.
    source_url: str = ""
    helpful_votes: int = 0
    total_votes: int = 0
    date_posted: Optional[datetime] = None
    date_updated: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if self.rating is not None and not (1 <= self.rating <= 5):
            raise ValueError("Rating must be between 1 and 5")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'book_id': self.book_id,
            'author_id': self.author_id,
            'author_name': self.author_name,
            'rating': self.rating,
            'title': self.title,
            'content': self.content,
            'source': self.source,
            'source_url': self.source_url,
            'helpful_votes': self.helpful_votes,
            'total_votes': self.total_votes,
            'date_posted': self.date_posted.isoformat() if self.date_posted else None,
            'date_updated': self.date_updated.isoformat() if self.date_updated else None,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Review':
        """Create Review from dictionary."""
        review = cls(
            id=data.get('id', str(uuid.uuid4())),
            book_id=data.get('book_id', ''),
            author_id=data.get('author_id', ''),
            author_name=data.get('author_name', ''),
            rating=data.get('rating'),
            title=data.get('title', ''),
            content=data.get('content', ''),
            source=data.get('source', ''),
            source_url=data.get('source_url', ''),
            helpful_votes=data.get('helpful_votes', 0),
            total_votes=data.get('total_votes', 0),
            metadata=data.get('metadata', {}),
        )
        
        for date_field in ['date_posted', 'date_updated', 'created_at']:
            if data.get(date_field):
                try:
                    setattr(review, date_field, datetime.fromisoformat(data[date_field]))
                except (ValueError, TypeError):
                    pass
        
        return review


@dataclass
class Rating:
    """Aggregated rating statistics for a book."""
    book_id: str = ""
    source: str = ""
    average: float = 0.0
    count: int = 0
    distribution: Dict[int, int] = field(default_factory=dict)  # star -> count
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'book_id': self.book_id,
            'source': self.source,
            'average': self.average,
            'count': self.count,
            'distribution': self.distribution,
            'last_updated': self.last_updated.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rating':
        """Create Rating from dictionary."""
        rating = cls(
            book_id=data.get('book_id', ''),
            source=data.get('source', ''),
            average=data.get('average', 0.0),
            count=data.get('count', 0),
            distribution=data.get('distribution', {}),
        )
        
        if data.get('last_updated'):
            try:
                rating.last_updated = datetime.fromisoformat(data['last_updated'])
            except (ValueError, TypeError):
                pass
        
        return rating


@dataclass
class Price:
    """Book price information."""
    book_id: str = ""
    source: str = ""
    price: float = 0.0
    currency: str = "USD"
    format: BookFormat = BookFormat.OTHER
    condition: str = "new"  # new, used, collectible
    url: str = ""
    availability: str = ""  # in_stock, out_of_stock, preorder
    last_checked: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'book_id': self.book_id,
            'source': self.source,
            'price': self.price,
            'currency': self.currency,
            'format': self.format.value,
            'condition': self.condition,
            'url': self.url,
            'availability': self.availability,
            'last_checked': self.last_checked.isoformat(),
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Price':
        """Create Price from dictionary."""
        price = cls(
            book_id=data.get('book_id', ''),
            source=data.get('source', ''),
            price=data.get('price', 0.0),
            currency=data.get('currency', 'USD'),
            format=BookFormat(data.get('format', 'other')),
            condition=data.get('condition', 'new'),
            url=data.get('url', ''),
            availability=data.get('availability', ''),
            metadata=data.get('metadata', {}),
        )
        
        if data.get('last_checked'):
            try:
                price.last_checked = datetime.fromisoformat(data['last_checked'])
            except (ValueError, TypeError):
                pass
        
        return price


@dataclass
class SearchResult:
    """Search result container."""
    query: str = ""
    total_results: int = 0
    books: List[Book] = field(default_factory=list)
    page: int = 1
    per_page: int = 20
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'query': self.query,
            'total_results': self.total_results,
            'books': [b.to_dict() for b in self.books],
            'page': self.page,
            'per_page': self.per_page,
            'source': self.source,
            'metadata': self.metadata,
        }