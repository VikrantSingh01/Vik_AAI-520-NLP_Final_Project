"""Required news prompt chain with explicit intermediate gates."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from faangm_research.schemas import EvidenceItem, Finding, NewsStageResult

TOPIC_TERMS = {
    "earnings_financials": {"earnings", "revenue", "profit", "margin", "sales"},
    "ai_capex_cloud": {
        "ai",
        "artificial intelligence",
        "cloud",
        "capex",
        "data center",
    },
    "product_strategy": {"launch", "product", "service", "subscription", "device"},
    "regulatory_legal": {"antitrust", "regulator", "lawsuit", "court", "legal"},
    "leadership_labor": {"ceo", "executive", "layoff", "jobs", "workforce"},
    "macro_market": {"inflation", "rates", "economy", "market", "recession"},
}
POSITIVE_TERMS = {"beat", "growth", "gain", "record", "strong", "surge", "profit"}
NEGATIVE_TERMS = {"miss", "decline", "loss", "risk", "cut", "lawsuit", "weak"}


def _stage(
    evidence_id: str,
    name: str,
    passed: bool,
    payload: dict[str, Any],
    message: str,
) -> NewsStageResult:
    return NewsStageResult(
        evidence_id=evidence_id,
        stage=name,
        passed_gate=passed,
        payload=payload,
        message=message,
    )


def run_news_chain(
    evidence: EvidenceItem,
    sentiment_override: str | None = None,
) -> tuple[list[NewsStageResult], Finding | None]:
    """Run Ingest -> Preprocess -> Classify -> Extract -> Summarize."""
    stages: list[NewsStageResult] = []
    ingested = bool(evidence.title and evidence.clean_text and str(evidence.url))
    stages.append(
        _stage(
            evidence.evidence_id,
            "ingest",
            ingested,
            {"title": evidence.title, "url": str(evidence.url)},
            "Required title, URL, and text are present"
            if ingested
            else "Missing input",
        )
    )
    if not ingested:
        return stages, None

    clean = re.sub(r"\s+", " ", evidence.clean_text).strip()
    preprocess_ok = 20 <= len(clean) <= 10_000
    stages.append(
        _stage(
            evidence.evidence_id,
            "preprocess",
            preprocess_ok,
            {"clean_text": clean, "character_count": len(clean)},
            "Whitespace normalized; numbers and negation preserved",
        )
    )
    if not preprocess_ok:
        return stages, None

    lowered = clean.lower()
    topic_scores = {
        topic: sum(term in lowered for term in terms)
        for topic, terms in TOPIC_TERMS.items()
    }
    topic = max(topic_scores, key=topic_scores.get)
    if topic_scores[topic] == 0:
        topic = "other"
    positive = sum(term in lowered for term in POSITIVE_TERMS)
    negative = sum(term in lowered for term in NEGATIVE_TERMS)
    lexical_sentiment = (
        "positive"
        if positive > negative
        else "negative"
        if negative > positive
        else "neutral"
    )
    sentiment = sentiment_override or lexical_sentiment
    stages.append(
        _stage(
            evidence.evidence_id,
            "classify",
            True,
            {
                "primary_topic": topic,
                "topic_scores": topic_scores,
                "sentiment": sentiment,
                "sentiment_method": (
                    "FinBERT" if sentiment_override else "lexical fallback"
                ),
                "lexical_sentiment": lexical_sentiment,
            },
            "Topic and sentiment are separate classifications",
        )
    )

    numeric_mentions = re.findall(
        r"(?:\$\s?)?\d+(?:\.\d+)?(?:\s?(?:%|billion|million|trillion))?",
        clean,
        flags=re.IGNORECASE,
    )
    aliases = {evidence.company.lower(), evidence.ticker.lower()}
    entities = sorted(alias for alias in aliases if alias in lowered)
    extracted = {
        "companies": entities or [evidence.ticker],
        "event": evidence.title,
        "numeric_mentions": numeric_mentions,
        "catalyst_or_risk": "risk"
        if sentiment == "negative"
        else "catalyst"
        if sentiment == "positive"
        else "context",
        "time_horizon": "recent",
        "sentiment": sentiment,
        "uncertainty": (
            "Headline and supplied summary only; full article was not ingested"
        ),
        "evidence_id": evidence.evidence_id,
    }
    numbers_supported = all(number in clean for number in numeric_mentions)
    stages.append(
        _stage(
            evidence.evidence_id,
            "extract",
            numbers_supported,
            extracted,
            "Every extracted number occurs in the source text",
        )
    )
    if not numbers_supported:
        return stages, None

    summary = f"{evidence.ticker}: {evidence.title} [{sentiment}; {topic}]"
    stages.append(
        _stage(
            evidence.evidence_id,
            "summarize",
            True,
            {"summary": summary, "evidence_ids": [evidence.evidence_id]},
            "Summary is source-linked and introduces no new number",
        )
    )
    finding = Finding(
        finding_id=f"FIND-{evidence.evidence_id}",
        ticker=evidence.ticker,
        category=f"news:{topic}",
        claim=summary,
        direction=sentiment,
        evidence_ids=[evidence.evidence_id],
        confidence=0.72 if topic != "other" else 0.55,
        limitations=[extracted["uncertainty"]],
    )
    return stages, finding


def stage_counts(results: list[NewsStageResult]) -> dict[str, int]:
    return dict(Counter(result.stage for result in results if result.passed_gate))
