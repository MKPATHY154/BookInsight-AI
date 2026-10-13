"""
Base Scraper Module
Provides abstract base class for all scrapers with rate limiting, session management, and error handling.
"""

import asyncio
import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from dataclasses import dataclass
from urllib.parse import urljoin
import random

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from bookinsight.config import config

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ScrapedData(Generic[T]):
    """Container for scraped data with metadata."""
    data: T
    source_url: str
    scraped_at: float
    scraper_name: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RateLimiter:
    """Token bucket rate limiter for controlling request frequency."""
    
    def __init__(self, rate: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            rate: Requests per second allowed
        """
        self.rate = rate
        self.tokens = rate
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            now = time.monotonic()
            # Add tokens based on time passed
            self.tokens = min(self.rate, self.tokens + (now - self.last_update) * self.rate)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return
            
            # Wait for next token
            wait_time = (1 - self.tokens) / self.rate
            self.tokens = 0
        
        await asyncio.sleep(wait_time)


class BaseScraper(ABC, Generic[T]):
    """
    Abstract base class for all scrapers.
    
    Provides:
    - Rate limiting
    - Session management with connection pooling
    - Automatic retries with exponential backoff
    - Request/response logging
    - Error handling
    """
    
    def __init__(
        self,
        name: str,
        base_url: str = "",
        rate_limit: Optional[float] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the scraper.
        
        Args:
            name: Unique name for this scraper
            base_url: Base URL for requests
            rate_limit: Requests per second (uses config default if None)
            timeout: Request timeout in seconds (uses config default if None)
            max_retries: Maximum retry attempts (uses config default if None)
            headers: Default headers for all requests
        """
        self.name = name
        self.base_url = base_url
        
        # Load settings from config
        scraper_settings = config.settings.scrapers
        self.rate_limit = rate_limit or scraper_settings.rate_limit
        self.timeout = timeout or scraper_settings.timeout
        self.max_retries = max_retries or scraper_settings.max_retries
        
        # Rate limiter
        self.rate_limiter = RateLimiter(self.rate_limit)
        
        # Session management
        self._session: Optional[ClientSession] = None
        self._session_lock = asyncio.Lock()
        
        # Default headers
        self.default_headers = {
            'User-Agent': scraper_settings.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        if headers:
            self.default_headers.update(headers)
        
        # Statistics
        self.stats = {
            'requests_made': 0,
            'requests_failed': 0,
            'bytes_downloaded': 0,
            'start_time': time.time(),
        }
    
    async def _get_session(self) -> ClientSession:
        """Get or create aiohttp session with connection pooling."""
        if self._session is None or self._session.closed:
            async with self._session_lock:
                if self._session is None or self._session.closed:
                    connector = TCPConnector(
                        limit=10,
                        limit_per_host=5,
                        ttl_dns_cache=300,
                        enable_cleanup_closed=True,
                    )
                    timeout = ClientTimeout(total=self.timeout)
                    self._session = ClientSession(
                        connector=connector,
                        timeout=timeout,
                        headers=self.default_headers,
                    )
        return self._session
    
    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def _build_url(self, path: str) -> str:
        """Build full URL from path."""
        return urljoin(self.base_url, path)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True
    )
    async def _request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Make an HTTP request with rate limiting and retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL or path relative to base_url
            **kwargs: Additional arguments passed to aiohttp request
            
        Returns:
            aiohttp.ClientResponse object
        """
        # Apply rate limiting
        await self.rate_limiter.acquire()
        
        # Build full URL if needed
        if not url.startswith(('http://', 'https://')):
            url = self._build_url(url)
        
        session = await self._get_session()
        
        # Add jitter to prevent thundering herd
        await asyncio.sleep(random.uniform(0, 0.1))
        
        start_time = time.time()
        try:
            response = await session.request(method, url, **kwargs)
            
            # Update statistics
            self.stats['requests_made'] += 1
            self.stats['bytes_downloaded'] += response.content_length or 0
            
            logger.debug(
                f"[{self.name}] {method} {url} - "
                f"Status: {response.status} - "
                f"Time: {time.time() - start_time:.2f}s"
            )
            
            return response
            
        except Exception as e:
            self.stats['requests_failed'] += 1
            logger.error(f"[{self.name}] Request failed: {method} {url} - {e}")
            raise
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make a GET request."""
        return await self._request('GET', url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make a POST request."""
        return await self._request('POST', url, **kwargs)
    
    async def get_text(self, url: str, **kwargs) -> str:
        """Make a GET request and return text content."""
        response = await self.get(url, **kwargs)
        return await response.text()
    
    async def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make a GET request and return JSON content."""
        response = await self.get(url, **kwargs)
        return await response.json()
    
    @abstractmethod
    async def scrape(self, *args, **kwargs) -> List[ScrapedData[T]]:
        """
        Main scraping method to be implemented by subclasses.
        
        Returns:
            List of ScrapedData objects
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraper statistics."""
        elapsed = time.time() - self.stats['start_time']
        return {
            **self.stats,
            'elapsed_time': elapsed,
            'requests_per_second': self.stats['requests_made'] / elapsed if elapsed > 0 else 0,
        }
    
    def reset_stats(self):
        """Reset scraper statistics."""
        self.stats = {
            'requests_made': 0,
            'requests_failed': 0,
            'bytes_downloaded': 0,
            'start_time': time.time(),
        }


class HTMLScraper(BaseScraper[str]):
    """Base scraper for HTML content with parsing utilities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parser = None
    
    @property
    def parser(self):
        """Lazy-load BeautifulSoup parser."""
        if self._parser is None:
            from bs4 import BeautifulSoup
            self._parser = BeautifulSoup
        return self._parser
    
    async def get_soup(self, url: str, **kwargs):
        """Get parsed BeautifulSoup object from URL."""
        html = await self.get_text(url, **kwargs)
        return self.parser(html, 'html.parser')
    
    def extract_text(self, element, selector: str = None, default: str = "") -> str:
        """Safely extract text from a BeautifulSoup element."""
        try:
            if selector:
                element = element.select_one(selector)
            if element:
                return element.get_text(strip=True)
        except Exception:
            pass
        return default
    
    def extract_attr(self, element, selector: str, attr: str, default: str = "") -> str:
        """Safely extract attribute from a BeautifulSoup element."""
        try:
            if selector:
                element = element.select_one(selector)
            if element and element.has_attr(attr):
                return element[attr]
        except Exception:
            pass
        return default
    
    def extract_all_text(self, element, selector: str) -> List[str]:
        """Extract text from all matching elements."""
        try:
            elements = element.select(selector)
            return [e.get_text(strip=True) for e in elements if e.get_text(strip=True)]
        except Exception:
            return []


class APIScraper(BaseScraper[Dict[str, Any]]):
    """Base scraper for JSON API endpoints."""
    
    async def get_json(self, url: str, params: Dict = None, **kwargs) -> Dict[str, Any]:
        """Make a GET request and return JSON with optional params."""
        if params:
            kwargs.setdefault('params', params)
        return await super().get_json(url, **kwargs)
    
    async def post_json(self, url: str, data: Dict = None, **kwargs) -> Dict[str, Any]:
        """Make a POST request with JSON data and return JSON response."""
        if data:
            kwargs.setdefault('json', data)
        response = await self.post(url, **kwargs)
        return await response.json()