"""SEC EDGAR collection with caching, provenance, and period validation."""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections.abc import Iterator
from datetime import UTC, date, datetime
from typing import Any

import requests
from bs4 import BeautifulSoup

from faangm_research.config import Company, Settings
from faangm_research.schemas import EvidenceItem, FinancialFact, SourceType

SEC_DATA = "https://data.sec.gov"
SEC_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"

CONCEPTS: dict[str, tuple[str, ...]] = {
    "revenue": (
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
    ),
    "operating_income": ("OperatingIncomeLoss",),
    "net_income": ("NetIncomeLoss",),
    "research_and_development": ("ResearchAndDevelopmentExpense",),
    "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities",),
    "capital_expenditures": (
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    ),
}


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class SecEdgarClient:
    """Small SEC client that respects fair-access guidance and records sources."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cache_dir = settings.data_dir / "raw" / "sec"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": settings.sec_user_agent,
                "Accept-Encoding": "gzip, deflate",
            }
        )
        self._last_request = 0.0

    def _request(self, url: str, cache_name: str) -> bytes:
        cache_path = self.cache_dir / cache_name
        if cache_path.exists():
            return cache_path.read_bytes()
        if self.settings.offline:
            raise FileNotFoundError(f"Offline cache is missing: {cache_path}")

        minimum_interval = 1.0 / self.settings.sec_requests_per_second
        wait = minimum_interval - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)

        last_error: Exception | None = None
        for retry in range(3):
            try:
                response = self.session.get(url, timeout=45)
                self._last_request = time.monotonic()
                response.raise_for_status()
                cache_path.write_bytes(response.content)
                return response.content
            except requests.RequestException as error:
                last_error = error
                if retry < 2:
                    time.sleep(2**retry)
        raise RuntimeError(f"SEC request failed for {url}") from last_error

    def get_company_facts(self, company: Company) -> dict[str, Any]:
        url = f"{SEC_DATA}/api/xbrl/companyfacts/CIK{company.cik}.json"
        content = self._request(url, f"{company.ticker}_companyfacts.json")
        return json.loads(content)

    def get_submissions(self, company: Company) -> dict[str, Any]:
        url = f"{SEC_DATA}/submissions/CIK{company.cik}.json"
        content = self._request(url, f"{company.ticker}_submissions.json")
        return json.loads(content)

    def annual_financial_facts(
        self,
        company: Company,
        years: int = 3,
    ) -> list[FinancialFact]:
        payload = self.get_company_facts(company)
        us_gaap = payload.get("facts", {}).get("us-gaap", {})
        selected: list[FinancialFact] = []

        for metric, candidates in CONCEPTS.items():
            annual = self._annual_metric_observations(us_gaap, candidates)
            for fiscal_year in sorted(annual, reverse=True)[:years]:
                concept, observation = annual[fiscal_year]
                accession = observation["accn"]
                selected.append(
                    FinancialFact(
                        company=company.name,
                        ticker=company.ticker,
                        metric=metric,
                        value=float(observation["val"]),
                        unit="USD",
                        period_start=date.fromisoformat(observation["start"]),
                        period_end=date.fromisoformat(observation["end"]),
                        fiscal_year=fiscal_year,
                        fiscal_period=str(observation.get("fp", "FY")),
                        form=str(observation["form"]),
                        filed_at=date.fromisoformat(observation["filed"]),
                        accession_number=accession,
                        xbrl_concept=concept,
                        source_url=self._filing_index_url(company, accession),
                    )
                )
        return selected

    def _annual_metric_observations(
        self,
        us_gaap: dict[str, Any],
        candidates: tuple[str, ...],
    ) -> dict[int, tuple[str, dict[str, Any]]]:
        selected: dict[int, tuple[int, str, dict[str, Any]]] = {}
        for priority, candidate in enumerate(candidates):
            if candidate not in us_gaap:
                continue
            observations = us_gaap[candidate].get("units", {}).get("USD", [])
            for observation in self._valid_annual_observations(observations):
                fiscal_year = int(observation["fy"])
                previous = selected.get(fiscal_year)
                if previous is None or priority < previous[0] or (
                    priority == previous[0]
                    and observation["filed"] > previous[2]["filed"]
                ):
                    selected[fiscal_year] = (priority, candidate, observation)
        return {
            fiscal_year: (candidate, observation)
            for fiscal_year, (_, candidate, observation) in selected.items()
        }

    def _valid_annual_observations(
        self,
        observations: list[dict[str, Any]],
    ) -> Iterator[dict[str, Any]]:
        for observation in observations:
            required = {"start", "end", "val", "fy", "filed", "accn", "form"}
            if not required.issubset(observation):
                continue
            if observation["form"] not in {"10-K", "10-K/A"}:
                continue
            start = date.fromisoformat(observation["start"])
            end = date.fromisoformat(observation["end"])
            duration = (end - start).days
            if 300 <= duration <= 430:
                yield observation

    def latest_filing_evidence(
        self,
        company: Company,
        form: str,
    ) -> EvidenceItem:
        submissions = self.get_submissions(company)
        recent = submissions["filings"]["recent"]
        rows = [
            dict(zip(recent, values, strict=True))
            for values in zip(*recent.values(), strict=True)
        ]
        filing = next(row for row in rows if row["form"] == form)
        accession = filing["accessionNumber"]
        primary_document = filing["primaryDocument"]
        url = (
            f"{SEC_ARCHIVES}/{int(company.cik)}/"
            f"{accession.replace('-', '')}/{primary_document}"
        )
        cache_name = f"{company.ticker}_{form.replace('-', '')}_{accession}.html"
        raw = self._request(url, cache_name)
        clean_text = self._html_to_text(raw)
        filed_at = date.fromisoformat(filing["filingDate"])
        evidence_id = f"SEC-{company.ticker}-{form}-{accession}"
        return EvidenceItem(
            evidence_id=evidence_id,
            company=company.name,
            ticker=company.ticker,
            source_type=SourceType.SEC,
            document_type=form,
            title=f"{company.name} {form} filed {filed_at.isoformat()}",
            period_end=date.fromisoformat(filing["reportDate"]),
            filing_date=filed_at,
            accession_number=accession,
            url=url,
            raw_text_hash=_sha256(raw),
            clean_text=clean_text,
            retrieved_at=datetime.now(UTC),
        )

    @staticmethod
    def _html_to_text(raw: bytes) -> str:
        soup = BeautifulSoup(raw, "html.parser")
        for element in soup(["script", "style", "noscript"]):
            element.decompose()
        text = soup.get_text(" ")
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _filing_index_url(company: Company, accession: str) -> str:
        return (
            f"{SEC_ARCHIVES}/{int(company.cik)}/"
            f"{accession.replace('-', '')}/{accession}-index.html"
        )
