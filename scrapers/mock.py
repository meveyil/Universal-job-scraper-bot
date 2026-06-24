"""Mock scraper with sample jobs for offline development and demos."""

from __future__ import annotations

from models import Job
from scrapers.base import BaseJobScraper


class MockJobScraper(BaseJobScraper):
    """Return a static demo dataset when real sources are unavailable."""

    name = "mock"

    async def fetch_jobs(self) -> list[Job]:
        """Return sample IT vacancies for framework demonstration."""
        return [
            Job(
                id="mock-python-001",
                title="Middle Python Developer",
                company="Acme Tech Labs",
                salary="800 000 – 1 200 000 ₸",
                link="https://example.com/jobs/mock-python-001",
                description=(
                    "Build backend services with Python and FastAPI. "
                    "Experience with PostgreSQL and REST APIs is required."
                ),
            ),
            Job(
                id="mock-frontend-002",
                title="Senior Frontend Engineer",
                company="Digital Studio",
                salary="900 000 – 1 400 000 ₸",
                link="https://example.com/jobs/mock-frontend-002",
                description=(
                    "React, TypeScript, and modern CSS. "
                    "You will implement UI from Figma and participate in code reviews."
                ),
            ),
            Job(
                id="mock-mobile-003",
                title="Flutter Mobile Developer",
                company="Mobile First KZ",
                salary="700 000 – 1 100 000 ₸",
                link="https://example.com/jobs/mock-mobile-003",
                description=(
                    "Cross-platform apps with Flutter and Dart. "
                    "Integrations with REST APIs and push notifications."
                ),
            ),
            Job(
                id="mock-devops-004",
                title="DevOps Engineer",
                company="CloudBridge",
                salary="1 100 000 – 1 800 000 ₸",
                link="https://example.com/jobs/mock-devops-004",
                description=(
                    "Kubernetes, Terraform, GitLab CI. "
                    "Monitoring with Prometheus and Grafana."
                ),
            ),
            Job(
                id="mock-java-005",
                title="Java Backend Developer",
                company="FinCore",
                salary="1 000 000 – 1 600 000 ₸",
                link="https://example.com/jobs/mock-java-005",
                description=(
                    "Microservices on Spring Boot, Kafka, and Docker. "
                    "Fintech experience is a plus."
                ),
            ),
        ]
