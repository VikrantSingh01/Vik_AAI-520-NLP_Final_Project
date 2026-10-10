"""Yahoo market and news adapter with reproducible CSV/JSON snapshots."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from faangm_research.config import Company, Settings
from faangm_research.schemas import EvidenceItem, SourceType


class YahooClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cache_dir = settings.data_dir / "raw" / "yahoo"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def prices(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        cache_path = self.cache_dir / f"prices_{start}_{end}.csv"
        if cache_path.exists():
            frame = pd.read_csv(cache_path, parse_dates=["Date"])
            return frame.set_index("Date")
        if self.settings.offline:
            raise FileNotFoundError(f"Offline cache is missing: {cache_path}")

        import yfinance as yf

        raw = yf.download(
            tickers,
            start=start,
            end=end,
            auto_adjust=True,
            progress=False,
            group_by="column",
        )
        close = (
            raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
        )
        if not isinstance(close, pd.DataFrame):
            close = close.to_frame(tickers[0])
        close.index.name = "Date"
        close.sort_index().to_csv(cache_path)
        return close.sort_index()

    def news(self, company: Company, limit: int | None = None) -> list[EvidenceItem]:
        item_limit = limit or self.settings.news_limit
        cache_path = self.cache_dir / f"{company.ticker}_news.json"
        if cache_path.exists():
            records = json.loads(cache_path.read_text(encoding="utf-8"))
        elif self.settings.offline:
            raise FileNotFoundError(f"Offline cache is missing: {cache_path}")
        else:
            import yfinance as yf

            records = yf.Ticker(company.ticker).get_news(count=item_limit)
            cache_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
        return [
            item
            for record in records[:item_limit]
            if (item := self._news_evidence(company, record)) is not None
        ]

    @staticmethod
    def _news_evidence(
        company: Company,
        record: dict[str, Any],
    ) -> EvidenceItem | None:
        content = record.get("content", record)
        title = str(content.get("title") or "").strip()
        summary = str(
            content.get("summary") or content.get("description") or ""
        ).strip()
        canonical = content.get("canonicalUrl") or content.get("clickThroughUrl") or {}
        url = canonical.get("url") if isinstance(canonical, dict) else canonical
        url = url or content.get("link")
        if not title or not url:
            return None

        published = content.get("pubDate") or content.get("providerPublishTime")
        if isinstance(published, int | float):
            published_at = datetime.fromtimestamp(published, tz=UTC)
        elif isinstance(published, str):
            published_at = datetime.fromisoformat(published.replace("Z", "+00:00"))
        else:
            published_at = None

        provider = content.get("provider", {})
        provider_name = (
            provider.get("displayName") if isinstance(provider, dict) else provider
        )
        clean_text = f"{title}. {summary}".strip()
        digest = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
        return EvidenceItem(
            evidence_id=f"NEWS-{company.ticker}-{digest[:12]}",
            company=company.name,
            ticker=company.ticker,
            source_type=SourceType.YAHOO,
            document_type="news",
            title=title,
            published_at=published_at,
            url=url,
            raw_text_hash=digest,
            clean_text=clean_text,
            retrieved_at=datetime.now(UTC),
            section=str(provider_name or "Unknown publisher"),
        )
