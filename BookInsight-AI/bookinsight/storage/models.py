"""
Database Models for BookInsight-AI
SQLAlchemy ORM models for persistent storage.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, Boolean,
    ForeignKey, Table, Index, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

Base = declarative_base()


# Association tables for many-to-many relationships
book_author = Table(
    'book_author',
    Base.metadata,
    Column('book_id', String(36), ForeignKey('books.id'), primary_key=True),
    Column('author_id', String(36), ForeignKey('authors.id'), primary_key=True),
)

book_subject = Table(
    'book_subject',
    Base.metadata,
    Column('book_id', String(36), ForeignKey('books.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('subjects.id'), primary_key=True),
)


class AuthorModel(Base):
    """SQLAlchemy model for Author."""
    __tablename__ = 'authors'
    
    id = Column(String(36), primary_key=True)
    name = Column(String(500), nullable=False, index=True)
    bio = Column(Text, default="")
    birth_date = Column(DateTime, nullable=True)
    death_date = Column(DateTime, nullable=True)
    website = Column(String(500), default="")
    photo_url = Column(String(500), default="")
    goodreads_id = Column(String(100), nullable=True, index=True)
    openlibrary_id = Column(String(100), nullable=True, index=True)
    wikipedia_url = Column(String(500), default="")
    metadata = Column(SQLiteJSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    books = relationship("BookModel", secondary=book_author, back_populates="authors")
    
    __table_args__ = (
        Index('ix_authors_name', 'name'),
        Index('ix_authors_goodreads_id', 'goodreads_id'),
        Index('ix_authors_openlibrary_id', 'openlibrary_id'),
    )
    
    def __repr__(self):
        return f"<AuthorModel(id={self.id}, name='{self.name}')>"


class SubjectModel(Base):
    """SQLAlchemy model for Subject/Genre."""
    __tablename__ = 'subjects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    books = relationship("BookModel", secondary=book_subject, back_populates="subjects")
    
    def __repr__(self):
        return f"<SubjectModel(id={self.id}, name='{self.name}')>"


class BookModel(Base):
    """SQLAlchemy model for Book."""
    __tablename__ = 'books'
    
    id = Column(String(36), primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    subtitle = Column(String(500), default="")
    isbn_10 = Column(String(13), nullable=True, index=True)
    isbn_13 = Column(String(13), nullable=True, index=True)
    publisher = Column(String(300), default="")
    publication_date = Column(DateTime, nullable=True)
    publication_year = Column(Integer, default=0, index=True)
    description = Column(Text, default="")
    page_count = Column(Integer, default=0)
    format = Column(String(50), default="other")
    language = Column(String(10), default="en")
    cover_url = Column(String(500), default="")
    cover_thumbnail_url = Column(String(500), default="")
    
    # External IDs
    goodreads_id = Column(String(100), nullable=True, index=True)
    google_books_id = Column(String(100), nullable=True, index=True)
    openlibrary_id = Column(String(100), nullable=True, index=True)
    librarything_id = Column(String(100), nullable=True)
    asin = Column(String(20), nullable=True, index=True)
    
    # Ratings
    average_rating = Column(Float, default=0.0)
    ratings_count = Column(Integer, default=0)
    reviews_count = Column(Integer, default=0)
    
    # Personal library fields
    my_rating = Column(Integer, nullable=True)
    my_review = Column(Text, default="")
    status = Column(String(50), default="want_to_read")
    date_started = Column(DateTime, nullable=True)
    date_finished = Column(DateTime, nullable=True)
    
    # Price
    price = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    price_url = Column(String(500), default="")
    
    # Metadata
    metadata = Column(SQLiteJSON, default=dict)
    source = Column(String(50), default="")
    source_url = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    authors = relationship("AuthorModel", secondary=book_author, back_populates="books")
    subjects = relationship("SubjectModel", secondary=book_subject, back_populates="books")
    reviews = relationship("ReviewModel", back_populates="book", cascade="all, delete-orphan")
    ratings = relationship("RatingModel", back_populates="book", cascade="all, delete-orphan")
    prices = relationship("PriceModel", back_populates="book", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_books_title', 'title'),
        Index('ix_books_isbn13', 'isbn_13'),
        Index('ix_books_isbn10', 'isbn_10'),
        Index('ix_books_goodreads_id', 'goodreads_id'),
        Index('ix_books_google_books_id', 'google_books_id'),
        Index('ix_books_openlibrary_id', 'openlibrary_id'),
        Index('ix_books_publication_year', 'publication_year'),
        Index('ix_books_status', 'status'),
        UniqueConstraint('isbn_13', name='uq_books_isbn13'),
        UniqueConstraint('isbn_10', name='uq_books_isbn10'),
    )
    
    def __repr__(self):
        return f"<BookModel(id={self.id}, title='{self.title}')>"


class ReviewModel(Base):
    """SQLAlchemy model for Review."""
    __tablename__ = 'reviews'
    
    id = Column(String(36), primary_key=True)
    book_id = Column(String(36), ForeignKey('books.id'), nullable=False, index=True)
    author_id = Column(String(36), default="")
    author_name = Column(String(300), default="")
    rating = Column(Integer, nullable=True)
    title = Column(String(500), default="")
    content = Column(Text, default="")
    source = Column(String(50), default="")
    source_url = Column(String(500), default="")
    helpful_votes = Column(Integer, default=0)
    total_votes = Column(Integer, default=0)
    date_posted = Column(DateTime, nullable=True)
    date_updated = Column(DateTime, nullable=True)
    metadata = Column(SQLiteJSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    book = relationship("BookModel", back_populates="reviews")
    
    __table_args__ = (
        Index('ix_reviews_book_id', 'book_id'),
        Index('ix_reviews_source', 'source'),
    )
    
    def __repr__(self):
        return f"<ReviewModel(id={self.id}, book_id={self.book_id}, rating={self.rating})>"


class RatingModel(Base):
    """SQLAlchemy model for aggregated Rating statistics."""
    __tablename__ = 'ratings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(String(36), ForeignKey('books.id'), nullable=False, index=True)
    source = Column(String(50), default="")
    average = Column(Float, default=0.0)
    count = Column(Integer, default=0)
    distribution = Column(SQLiteJSON, default=dict)  # {1: count, 2: count, ...}
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    book = relationship("BookModel", back_populates="ratings")
    
    __table_args__ = (
        Index('ix_ratings_book_id', 'book_id'),
        Index('ix_ratings_source', 'source'),
        UniqueConstraint('book_id', 'source', name='uq_ratings_book_source'),
    )
    
    def __repr__(self):
        return f"<RatingModel(book_id={self.book_id}, source={self.source}, avg={self.average})>"


class PriceModel(Base):
    """SQLAlchemy model for Price information."""
    __tablename__ = 'prices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(String(36), ForeignKey('books.id'), nullable=False, index=True)
    source = Column(String(50), default="")
    price = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    format = Column(String(50), default="other")
    condition = Column(String(50), default="new")
    url = Column(String(500), default="")
    availability = Column(String(50), default="")
    last_checked = Column(DateTime, default=datetime.utcnow)
    metadata = Column(SQLiteJSON, default=dict)
    
    # Relationships
    book = relationship("BookModel", back_populates="prices")
    
    __table_args__ = (
        Index('ix_prices_book_id', 'book_id'),
        Index('ix_prices_source', 'source'),
    )
    
    def __repr__(self):
        return f"<PriceModel(book_id={self.book_id}, source={self.source}, price={self.price})>"