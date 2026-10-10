"""Project configuration and company metadata."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Company:
    name: str
    ticker: str
    cik: str
    aliases: tuple[str, ...]


COMPANIES: tuple[Company, ...] = (
    Company("Meta Platforms", "META", "0001326801", ("Meta", "Facebook")),
    Company("Apple", "AAPL", "0000320193", ("Apple Inc.",)),
    Company("Amazon", "AMZN", "0001018724", ("Amazon.com", "AWS")),
    Company("Netflix", "NFLX", "0001065280", ("Netflix, Inc.",)),
    Company("Alphabet", "GOOGL", "0001652044", ("Google", "GOOG")),
    Company("Microsoft", "MSFT", "0000789019", ("Microsoft Corp.",)),
)

COMPANY_BY_TICKER = {company.ticker: company for company in COMPANIES}


@dataclass(frozen=True, slots=True)
class Settings:
    root: Path
    as_of_date: date
    seed: int = 520
    benchmark: str = "QQQ"
    news_limit: int = 10
    sec_requests_per_second: float = 5.0
    max_revisions: int = 2
    offline: bool = False

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def output_dir(self) -> Path:
        return self.root / "outputs"

    @property
    def sec_user_agent(self) -> str:
        return os.getenv(
            "SEC_USER_AGENT",
            "AAI-520 academic project contact@example.com",
        )

    @classmethod
    def default(cls, root: Path | None = None, offline: bool = False) -> Settings:
        project_root = root or Path(__file__).resolve().parents[2]
        return cls(root=project_root, as_of_date=date(2026, 9, 7), offline=offline)
