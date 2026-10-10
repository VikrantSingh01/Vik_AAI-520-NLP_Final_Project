"""Serialization helpers for reproducible research snapshots."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from faangm_research.schemas import EvidenceItem, FinancialFact


def save_snapshot(
    output_dir: Path,
    facts: list[FinancialFact],
    evidence: list[EvidenceItem],
    prices: pd.DataFrame,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "financial_facts.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in facts], indent=2),
        encoding="utf-8",
    )
    (output_dir / "source_evidence.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in evidence], indent=2),
        encoding="utf-8",
    )
    prices.to_csv(output_dir / "prices.csv", index_label="Date")


def load_snapshot(
    input_dir: Path,
) -> tuple[list[FinancialFact], list[EvidenceItem], pd.DataFrame]:
    facts = [
        FinancialFact.model_validate(item)
        for item in json.loads((input_dir / "financial_facts.json").read_text())
    ]
    evidence = [
        EvidenceItem.model_validate(item)
        for item in json.loads((input_dir / "source_evidence.json").read_text())
    ]
    prices = pd.read_csv(input_dir / "prices.csv", parse_dates=["Date"]).set_index(
        "Date"
    )
    return facts, evidence, prices
