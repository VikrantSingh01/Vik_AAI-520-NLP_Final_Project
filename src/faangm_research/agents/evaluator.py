"""Hybrid deterministic evaluator for the evaluator-optimizer workflow."""

from __future__ import annotations

import json
import re

from faangm_research.schemas import (
    EvaluationResult,
    EvidenceItem,
    ReportClaim,
    ResearchReport,
)

NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?%?")


def numeric_claim_consistent(
    claim: ReportClaim,
    evidence_by_id: dict[str, EvidenceItem],
) -> bool:
    claim_text = re.sub(r"\b10-[KQ]\b", "", claim.text)
    tokens = NUMBER_PATTERN.findall(claim_text)
    if not tokens:
        return True
    evidence = [
        evidence_by_id[item] for item in claim.evidence_ids if item in evidence_by_id
    ]
    if not evidence:
        return False

    plain_text = " ".join(
        f"{item.title} {item.document_type} {item.clean_text}" for item in evidence
    )
    numeric_values: list[float] = []
    percentage_values: list[float] = []
    for item in evidence:
        try:
            payload = json.loads(item.clean_text)
        except json.JSONDecodeError:
            payload = {}
        for value in payload.values():
            if isinstance(value, int | float) and not isinstance(value, bool):
                numeric_values.append(float(value))
                if abs(value) <= 2:
                    percentage_values.append(float(value) * 100)
        if "AI-related tokens" in claim.text:
            words = item.clean_text.lower().split()
            count = sum(word in {"ai", "artificial", "intelligence"} for word in words)
            numeric_values.extend([float(count), count / max(len(words), 1) * 10_000])

    for token in tokens:
        if token in plain_text:
            continue
        if token.endswith("%"):
            target = float(token[:-1])
            if not any(abs(target - value) <= 0.051 for value in percentage_values):
                return False
        else:
            target = float(token)
            numeric_match = any(
                abs(target - value) <= 0.051 for value in numeric_values
            )
            if not numeric_match:
                return False
    return True


def numeric_consistency_score(
    report: ResearchReport,
    evidence_by_id: dict[str, EvidenceItem],
) -> float:
    numeric_claims = [
        claim for claim in report.claims if NUMBER_PATTERN.search(claim.text)
    ]
    if not numeric_claims:
        return 1.0
    return sum(
        numeric_claim_consistent(claim, evidence_by_id) for claim in numeric_claims
    ) / len(numeric_claims)


def evaluate_report(
    report: ResearchReport,
    evidence_registry: set[str] | dict[str, EvidenceItem],
    expected_tickers: set[str],
) -> EvaluationResult:
    valid_evidence_ids = set(evidence_registry)
    claim_count = len(report.claims)
    cited = sum(
        bool(claim.evidence_ids)
        and all(item in valid_evidence_ids for item in claim.evidence_ids)
        for claim in report.claims
    )
    citation_coverage = cited / claim_count if claim_count else 0.0
    represented = {
        ticker
        for ticker in expected_tickers
        if any(ticker in claim.text for claim in report.claims)
    }
    question_coverage = (
        len(represented) / len(expected_tickers) if expected_tickers else 1.0
    )
    balance = float(bool(report.catalysts) and bool(report.risks))
    numeric_consistency = (
        numeric_consistency_score(report, evidence_registry)
        if isinstance(evidence_registry, dict)
        else 1.0
    )
    groundedness = citation_coverage
    freshness = float(bool(report.as_of_date))
    style = float("not investment advice" in report.disclaimer.lower())
    total = 100 * (
        0.25 * citation_coverage
        + 0.20 * numeric_consistency
        + 0.20 * groundedness
        + 0.10 * balance
        + 0.10 * freshness
        + 0.10 * question_coverage
        + 0.05 * style
    )
    issues: list[str] = []
    feedback: list[str] = []
    if citation_coverage < 0.95:
        issues.append("Material claims lack valid evidence IDs")
    if numeric_consistency < 1.0:
        issues.append(
            "One or more displayed numbers do not reconcile to cited evidence"
        )
    if question_coverage < 1.0:
        issues.append("Not every requested ticker is represented")
    if report.revision == 0:
        feedback.append("Add explicit source-type separation and uncertainty language")
    if issues:
        decision = "request_evidence"
    elif report.revision == 0:
        decision = "revise"
    elif total >= 85:
        decision = "accept"
    else:
        decision = "revise"
    return EvaluationResult(
        decision=decision,
        total_score=total,
        citation_coverage=citation_coverage,
        numeric_consistency=numeric_consistency,
        groundedness=groundedness,
        analytical_balance=balance,
        freshness=freshness,
        question_coverage=question_coverage,
        style_uncertainty=style,
        critical_issues=issues,
        feedback=feedback,
    )
