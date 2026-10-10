"""Collect and freeze the primary data used by the final notebook."""

from __future__ import annotations

import argparse
from datetime import timedelta

from faangm_research.config import COMPANIES, Settings
from faangm_research.provenance import build_manifest
from faangm_research.snapshot import save_snapshot
from faangm_research.tools import SecEdgarClient, YahooClient


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-filings", action="store_true")
    parser.add_argument("--news-limit", type=int, default=10)
    args = parser.parse_args()

    settings = Settings.default()
    sec = SecEdgarClient(settings)
    yahoo = YahooClient(settings)
    facts = []
    evidence = []
    warnings = []
    for company in COMPANIES:
        print(f"Collecting {company.ticker}...")
        facts.extend(sec.annual_financial_facts(company))
        if not args.skip_filings:
            for form in ("10-K", "10-Q"):
                try:
                    evidence.append(sec.latest_filing_evidence(company, form))
                except (
                    KeyError,
                    StopIteration,
                    FileNotFoundError,
                    RuntimeError,
                ) as error:
                    warnings.append(f"{company.ticker} {form}: {error}")
        try:
            evidence.extend(yahoo.news(company, limit=args.news_limit))
        except (FileNotFoundError, RuntimeError, ValueError) as error:
            warnings.append(f"{company.ticker} news: {error}")

    start = (settings.as_of_date - timedelta(days=370)).isoformat()
    end = (settings.as_of_date + timedelta(days=1)).isoformat()
    tickers = [company.ticker for company in COMPANIES] + [settings.benchmark]
    prices = yahoo.prices(tickers, start=start, end=end)
    processed = settings.data_dir / "processed"
    save_snapshot(processed, facts, evidence, prices)
    manifest = build_manifest(settings.data_dir, settings.data_dir / "manifest.json")
    print(
        f"Saved {len(facts)} facts, {len(evidence)} evidence items, "
        f"{len(prices)} price rows, and {manifest['file_count']} manifest entries."
    )
    for warning in warnings:
        print(f"WARNING: {warning}")


if __name__ == "__main__":
    main()
