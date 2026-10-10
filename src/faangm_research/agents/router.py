"""Constrained content routing with an auditable deterministic fallback."""

from __future__ import annotations

from faangm_research.schemas import EvidenceItem, Route, RouteDecision, SourceType


def route_evidence(evidence: EvidenceItem) -> RouteDecision:
    document_type = evidence.document_type.lower()
    text = f"{evidence.title} {evidence.clean_text[:500]}".lower()
    if evidence.source_type == SourceType.SEC or document_type in {
        "10-k",
        "10-q",
        "8-k",
    }:
        route = Route.FILING
        tools = ["filing_retrieval", "xbrl_lookup"]
        reason = "SEC source or filing form"
    elif document_type == "news":
        route = Route.NEWS
        tools = ["news_chain"]
        reason = "News document metadata"
    elif evidence.source_type == SourceType.FRED or any(
        term in text for term in ("inflation", "federal funds", "treasury yield", "gdp")
    ):
        route = Route.MACRO
        tools = ["macro_analysis"]
        reason = "Macro source or economic-series terminology"
    elif document_type in {"prices", "market_summary", "event_return"}:
        route = Route.MARKET
        tools = ["market_analytics"]
        reason = "Market data product"
    else:
        route = Route.MIXED
        tools = ["filing_retrieval", "news_chain"]
        reason = "No single specialist dominates"
    return RouteDecision(
        item_id=evidence.evidence_id,
        route=route,
        confidence=0.98 if route != Route.MIXED else 0.55,
        reason=reason,
        required_tools=tools,
        used_fallback=True,
    )
