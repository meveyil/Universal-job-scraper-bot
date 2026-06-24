"""Example HTML scraper skeleton for custom job boards."""

from __future__ import annotations

import logging

import aiohttp

from models import Job
from scrapers.base import BaseJobScraper

logger = logging.getLogger(__name__)


class HtmlJobScraper(BaseJobScraper):
    """
    Template scraper for HTML-based job boards.

    Override ``fetch_jobs`` to parse a target website with aiohttp
    (and optionally BeautifulSoup/lxml in your own implementation).
    """

    name = "html"

    def __init__(self, source_url: str = "") -> None:
        self.source_url = source_url

    async def fetch_jobs(self) -> list[Job]:
        """
        Fetch and parse jobs from an HTML page.

        This skeleton demonstrates the extension point. Implement parsing
        logic for your target site and map fields to the Job dataclass.
        """
        if not self.source_url:
            logger.warning("HtmlJobScraper: SOURCE_URL is not configured")
            return []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.source_url, timeout=15) as response:
                    response.raise_for_status()
                    await response.text()
        except aiohttp.ClientError as exc:
            logger.error("HtmlJobScraper request failed: %s", exc)
            return []

        # TODO: parse HTML and return Job instances.
        return []
