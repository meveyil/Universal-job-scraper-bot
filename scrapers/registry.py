"""Scraper registry and factory."""

from __future__ import annotations

from config import SCRAPER_SOURCE
from scrapers.base import BaseJobScraper
from scrapers.html_scraper import HtmlJobScraper
from scrapers.mock import MockJobScraper

SCRAPER_REGISTRY: dict[str, type[BaseJobScraper]] = {
    "mock": MockJobScraper,
    "html": HtmlJobScraper,
}


def get_scraper(source: str | None = None) -> BaseJobScraper:
    """
    Return a scraper instance for the given source name.

    Args:
        source: Scraper key (defaults to SCRAPER_SOURCE from config).

    Raises:
        ValueError: If the scraper name is not registered.
    """
    name = (source or SCRAPER_SOURCE).lower()
    scraper_cls = SCRAPER_REGISTRY.get(name)
    if scraper_cls is None:
        available = ", ".join(sorted(SCRAPER_REGISTRY))
        raise ValueError(f"Unknown scraper '{name}'. Available: {available}")
    return scraper_cls()
