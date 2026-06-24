"""Pluggable job scraper modules."""

from scrapers.base import BaseJobScraper
from scrapers.mock import MockJobScraper
from scrapers.registry import get_scraper

__all__ = ["BaseJobScraper", "MockJobScraper", "get_scraper"]
