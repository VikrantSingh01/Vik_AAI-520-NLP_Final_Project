"""Evaluation utilities for routes, retrieval, reports, and memory behavior."""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from faangm_research.agents.evaluator import numeric_claim_consistent


def classification_metrics(
    expected: list[str],
    predicted: list[str],
) -> dict[str, float]:
    precision, recall, f1, _ = precision_recall_fscore_support(
        expected,
        predicted,
        average="macro",
        zero_division=0,
    )
    return {
        "accuracy": float(accuracy_score(expected, predicted)),
        "macro_precision": float(precision),
        "macro_recall": float(recall),
        "macro_f1": float(f1),
    }


def memory_comparison(cold: dict, warm: dict) -> pd.DataFrame:
    records = []
    for label, state in (("cold", cold), ("warm", warm)):
        evaluation = state["evaluations"][-1]
        records.append(
            {
                "run": label,
                "memory_records_used": len(state.get("memory_used", [])),
                "fallback_lookups": state.get("fallback_lookups", 0),
                "revisions": state.get("revision_count", 0),
                "quality_score": evaluation.total_score,
                "accepted": evaluation.decision == "accept",
            }
        )
    return pd.DataFrame(records)


def report_claim_audit(state: dict) -> pd.DataFrame:
    evidence_by_id = {item.evidence_id: item for item in state["evidence"]}
    return pd.DataFrame(
        [
            {
                "claim_id": claim.claim_id,
                "claim": claim.text,
                "citation_count": len(claim.evidence_ids),
                "citations_valid": all(
                    item in evidence_by_id for item in claim.evidence_ids
                ),
                "numbers_reconciled": numeric_claim_consistent(claim, evidence_by_id),
            }
            for claim in state["report"].claims
        ]
    )
