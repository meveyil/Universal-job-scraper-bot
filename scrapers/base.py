"""Abstract base class for job scraper modules."""

from __future__ import annotations

from abc import ABC, abstractmethod

from models import Job


class BaseJobScraper(ABC):
    """Interface that every job source scraper must implement."""

    name: str = "base"

    @abstractmethod
    async def fetch_jobs(self) -> list[Job]:
        """
        Fetch job postings from a specific source.

        Returns:
            A list of normalized Job objects.
        """
