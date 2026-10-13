"""
BookInsight-AI Configuration Module
Handles loading and managing application settings from YAML files.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from dataclasses import dataclass, field


@dataclass
class ScraperSettings:
    """Settings for web scrapers."""
    rate_limit: float = 1.0
    timeout: int = 30
    max_retries: int = 3
    user_agent: str = "BookInsight-AI/1.0"


@dataclass
class GoodreadsSettings:
    """Goodreads-specific settings."""
    enabled: bool = True
    base_url: str = "https://www.goodreads.com"


@dataclass
class GoogleBooksSettings:
    """Google Books API settings."""
    enabled: bool = True
    api_key: str = ""
    base_url: str = "https://www.googleapis.com/books/v1"
    max_results: int = 40


@dataclass
class OpenLibrarySettings:
    """Open Library settings."""
    enabled: bool = True
    base_url: str = "https://openlibrary.org"
    covers_base_url: str = "https://covers.openlibrary.org"


@dataclass
class DatabaseSettings:
    """Database settings."""
    type: str = "sqlite"
    path: str = "data/bookinsight.db"
    echo: bool = False


@dataclass
class ExportSettings:
    """Export settings."""
    default_format: str = "json"
    output_dir: str = "exports"
    formats: list = field(default_factory=lambda: ["json", "csv", "excel"])


@dataclass
class LoggingSettings:
    """Logging settings."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/bookinsight.log"


@dataclass
class Settings:
    """Main application settings."""
    scrapers: ScraperSettings = field(default_factory=ScraperSettings)
    goodreads: GoodreadsSettings = field(default_factory=GoodreadsSettings)
    google_books: GoogleBooksSettings = field(default_factory=GoogleBooksSettings)
    openlibrary: OpenLibrarySettings = field(default_factory=OpenLibrarySettings)
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    export: ExportSettings = field(default_factory=ExportSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)


class Config:
    """Configuration manager for BookInsight-AI."""
    
    _instance: Optional['Config'] = None
    _settings: Optional[Settings] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._settings is None:
            self.load()
    
    def load(self, config_path: Optional[str] = None) -> Settings:
        """Load configuration from YAML file."""
        if config_path is None:
            # Look for config files in order of precedence
            config_paths = [
                Path("config/local.yaml"),
                Path("config/settings.yaml"),
                Path(__file__).parent.parent / "config" / "settings.yaml",
            ]
            
            for path in config_paths:
                if path.exists():
                    config_path = str(path)
                    break
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        else:
            config_data = {}
        
        self._settings = self._parse_config(config_data)
        return self._settings
    
    def _parse_config(self, data: Dict[str, Any]) -> Settings:
        """Parse configuration dictionary into Settings object."""
        settings = Settings()
        
        if 'scrapers' in data:
            s = data['scrapers']
            settings.scrapers = ScraperSettings(
                rate_limit=s.get('rate_limit', 1.0),
                timeout=s.get('timeout', 30),
                max_retries=s.get('max_retries', 3),
                user_agent=s.get('user_agent', "BookInsight-AI/1.0")
            )
        
        if 'goodreads' in data:
            g = data['goodreads']
            settings.goodreads = GoodreadsSettings(
                enabled=g.get('enabled', True),
                base_url=g.get('base_url', "https://www.goodreads.com")
            )
        
        if 'google_books' in data:
            gb = data['google_books']
            settings.google_books = GoogleBooksSettings(
                enabled=gb.get('enabled', True),
                api_key=gb.get('api_key', ""),
                base_url=gb.get('base_url', "https://www.googleapis.com/books/v1"),
                max_results=gb.get('max_results', 40)
            )
        
        if 'openlibrary' in data:
            ol = data['openlibrary']
            settings.openlibrary = OpenLibrarySettings(
                enabled=ol.get('enabled', True),
                base_url=ol.get('base_url', "https://openlibrary.org"),
                covers_base_url=ol.get('covers_base_url', "https://covers.openlibrary.org")
            )
        
        if 'database' in data:
            db = data['database']
            settings.database = DatabaseSettings(
                type=db.get('type', "sqlite"),
                path=db.get('path', "data/bookinsight.db"),
                echo=db.get('echo', False)
            )
        
        if 'export' in data:
            e = data['export']
            settings.export = ExportSettings(
                default_format=e.get('default_format', "json"),
                output_dir=e.get('output_dir', "exports"),
                formats=e.get('formats', ["json", "csv", "excel"])
            )
        
        if 'logging' in data:
            l = data['logging']
            settings.logging = LoggingSettings(
                level=l.get('level', "INFO"),
                format=l.get('format', "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
                file=l.get('file', "logs/bookinsight.log")
            )
        
        return settings
    
    @property
    def settings(self) -> Settings:
        """Get current settings."""
        if self._settings is None:
            self.load()
        return self._settings
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value by dot-notation key."""
        keys = key.split('.')
        value = self.settings
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default
        return value


# Global config instance
config = Config()