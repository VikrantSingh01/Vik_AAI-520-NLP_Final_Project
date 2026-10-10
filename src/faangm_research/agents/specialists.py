"""Evidence-bound filing, financial, market, and news specialist logic."""

from __future__ import annotations

from collections import Counter

import pandas as pd

from faangm_research.schemas import EvidenceItem, Finding, NewsStageResult
from faangm_research.workflows.news_chain import run_news_chain


def filing_findings(evidence: list[EvidenceItem]) -> list[Finding]:
    findings: list[Finding] = []
    for item in evidence:
        if item.document_type not in {"10-K", "10-Q", "8-K"}:
            continue
        words = item.clean_text.lower().split()
        ai_count = sum(word in {"ai", "artificial", "intelligence"} for word in words)
        intensity = ai_count / max(len(words), 1) * 10_000
        findings.append(
            Finding(
                finding_id=f"FILING-{item.ticker}-{item.document_type}",
                ticker=item.ticker,
                category="filing_narrative",
                claim=(
                    f"{item.ticker} {item.document_type} contains {ai_count} "
                    "AI-related "
                    f"tokens ({intensity:.1f} per 10,000 words)."
                ),
                direction="neutral",
                evidence_ids=[item.evidence_id],
                confidence=0.9,
                limitations=["Token frequency measures emphasis, not economic value"],
            )
        )
    return findings


def financial_findings(panel: pd.DataFrame) -> list[Finding]:
    findings: list[Finding] = []
    if panel.empty:
        return findings
    for ticker, group in panel.groupby("ticker"):
        row = group.sort_values("fiscal_year").iloc[-1]
        direction = "positive" if row.get("fcf_margin", 0) > 0 else "negative"
        claim = (
            f"{ticker} FY{int(row['fiscal_year'])}: revenue growth "
            f"{row.get('revenue_growth', float('nan')):.1%}, operating margin "
            f"{row.get('operating_margin', float('nan')):.1%}, FCF margin "
            f"{row.get('fcf_margin', float('nan')):.1%}, and capex intensity "
            f"{row.get('capex_intensity', float('nan')):.1%}."
        )
        findings.append(
            Finding(
                finding_id=f"FIN-{ticker}-{int(row['fiscal_year'])}",
                ticker=ticker,
                category="financial_execution",
                claim=claim,
                direction=direction,
                evidence_ids=[f"FACTS-{ticker}-{int(row['fiscal_year'])}"],
                confidence=0.98,
                limitations=["FCF is operating cash flow minus capital expenditures"],
            )
        )
    return findings


def market_findings(summary: pd.DataFrame) -> list[Finding]:
    findings: list[Finding] = []
    for row in summary.itertuples(index=False):
        if row.ticker == "QQQ":
            continue
        direction = "positive" if row.benchmark_excess_return > 0 else "negative"
        findings.append(
            Finding(
                finding_id=f"MKT-{row.ticker}",
                ticker=row.ticker,
                category="market_confirmation",
                claim=(
                    f"{row.ticker} returned {row.total_return:.1%}, with "
                    f"{row.annualized_volatility:.1%} annualized volatility, "
                    f"{row.max_drawdown:.1%} maximum drawdown, and "
                    f"{row.benchmark_excess_return:.1%} excess return versus QQQ."
                ),
                direction=direction,
                evidence_ids=[f"MARKET-{row.ticker}"],
                confidence=0.98,
                limitations=["Descriptive association; not causal attribution"],
            )
        )
    return findings


def news_findings(
    evidence: list[EvidenceItem],
    sentiment_overrides: dict[str, str] | None = None,
) -> tuple[list[Finding], list[NewsStageResult]]:
    findings: list[Finding] = []
    stages: list[NewsStageResult] = []
    seen_hashes: Counter[str] = Counter()
    for item in evidence:
        if item.document_type != "news":
            continue
        seen_hashes[item.raw_text_hash] += 1
        if seen_hashes[item.raw_text_hash] > 1:
            continue
        sentiment = (sentiment_overrides or {}).get(item.evidence_id)
        item_stages, finding = run_news_chain(item, sentiment_override=sentiment)
        stages.extend(item_stages)
        if finding:
            findings.append(finding)
    return findings, stages
