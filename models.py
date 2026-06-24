"""Shared data models for job postings."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Job:
    """Normalized job posting used across all scraper modules."""

    id: str
    title: str
    company: str
    salary: str
    link: str
    description: str
