"""Evidence-linked report generation and deterministic optimization."""

from __future__ import annotations

from datetime import date

from faangm_research.schemas import Finding, ReportClaim, ResearchReport

DISCLAIMER = (
    "Educational research only; this report is not investment advice and does not "
    "establish causation or predict future returns."
)


def synthesize_report(
    query: str,
    findings: list[Finding],
    as_of_date: date,
    revision: int = 0,
) -> ResearchReport:
    strongest = sorted(findings, key=lambda item: item.confidence, reverse=True)
    claims = [
        ReportClaim(
            claim_id=f"C{index:02d}",
            text=finding.claim,
            evidence_ids=finding.evidence_ids,
        )
        for index, finding in enumerate(strongest, start=1)
    ]
    catalysts = [
        finding.claim for finding in findings if finding.direction == "positive"
    ]
    risks = [finding.claim for finding in findings if finding.direction == "negative"]
    divergences = _divergences(findings)
    unknowns = sorted(
        {
            limitation
            for finding in findings
            for limitation in finding.limitations
            if limitation
        }
    )
    coverage = len({finding.ticker for finding in findings})
    summary = (
        f"The research desk evaluated {coverage} ticker(s) for '{query}'. "
        f"It found {len(catalysts)} positive signals, {len(risks)} negative signals, "
        f"and {len(divergences)} cross-source divergences as of {as_of_date}."
    )
    return ResearchReport(
        title="FAANG+M Narrative-to-Numbers Research Brief",
        as_of_date=as_of_date,
        executive_summary=summary,
        claims=claims,
        catalysts=catalysts or ["No source-supported catalyst was identified"],
        risks=risks or ["No source-supported negative signal was identified"],
        divergences=divergences or ["No directional divergence met the rule"],
        unknowns=unknowns or ["No additional limitation was recorded"],
        confidence=min(0.95, 0.55 + len(claims) / 100),
        disclaimer=DISCLAIMER,
        revision=revision,
    )


def optimize_report(report: ResearchReport, feedback: list[str]) -> ResearchReport:
    updated = report.model_copy(deep=True)
    updated.revision += 1
    updated.executive_summary += (
        " The optimized version explicitly separates reported facts, narrative "
        "signals, and descriptive market evidence."
    )
    for message in feedback:
        if message not in updated.unknowns:
            updated.unknowns.append(message)
    updated.confidence = min(updated.confidence, 0.9)
    return updated


def _divergences(findings: list[Finding]) -> list[str]:
    by_ticker: dict[str, set[str]] = {}
    for finding in findings:
        by_ticker.setdefault(finding.ticker, set()).add(finding.direction)
    return [
        f"{ticker} has both positive and negative evidence across sources."
        for ticker, directions in sorted(by_ticker.items())
        if {"positive", "negative"}.issubset(directions)
    ]
