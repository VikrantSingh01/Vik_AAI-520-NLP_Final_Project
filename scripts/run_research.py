"""Execute cold/warm FAANG+M graph runs from the frozen snapshot."""

from __future__ import annotations

import json

import pandas as pd

from faangm_research.agents.memory import ResearchMemory
from faangm_research.config import Settings
from faangm_research.evaluation import memory_comparison, report_claim_audit
from faangm_research.graph import run_research
from faangm_research.schemas import PlanStep
from faangm_research.snapshot import load_snapshot

QUERY = (
    "Compare FAANG+M and identify the largest gaps between AI narrative, capital "
    "commitment, cash-flow support, news sentiment, and market reaction."
)


def serializable_state(state: dict) -> dict:
    excluded = {"facts", "prices", "evidence"}
    return {
        key: [item.model_dump(mode="json") for item in value]
        if isinstance(value, list) and value and hasattr(value[0], "model_dump")
        else value.model_dump(mode="json")
        if hasattr(value, "model_dump")
        else value
        for key, value in state.items()
        if key not in excluded
    }


def main() -> None:
    settings = Settings.default(offline=True)
    facts, evidence, prices = load_snapshot(settings.data_dir / "processed")
    memory = ResearchMemory(settings.output_dir / "memory" / "agent_memory.sqlite")
    memory.reset()
    plan_path = settings.output_dir / "model" / "validated_qwen_plan.json"
    plan_override = None
    if plan_path.exists():
        plan_override = [
            PlanStep.model_validate(item)
            for item in json.loads(plan_path.read_text(encoding="utf-8"))
        ]
    sentiment_path = settings.output_dir / "model" / "finbert_sentiment.csv"
    sentiment_overrides = {}
    if sentiment_path.exists():
        sentiment_frame = pd.read_csv(sentiment_path)
        sentiment_overrides = dict(
            zip(
                sentiment_frame["evidence_id"],
                sentiment_frame["label"],
                strict=True,
            )
        )
    cold = run_research(
        QUERY,
        facts,
        prices,
        evidence,
        settings,
        memory,
        run_label="cold",
        plan_override=plan_override,
        sentiment_overrides=sentiment_overrides,
    )
    warm = run_research(
        QUERY,
        facts,
        prices,
        evidence,
        settings,
        memory,
        run_label="warm",
        plan_override=plan_override,
        sentiment_overrides=sentiment_overrides,
    )
    traces = settings.output_dir / "traces"
    tables = settings.output_dir / "tables"
    traces.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    (traces / "cold_run.json").write_text(
        json.dumps(serializable_state(cold), indent=2), encoding="utf-8"
    )
    (traces / "warm_run.json").write_text(
        json.dumps(serializable_state(warm), indent=2), encoding="utf-8"
    )
    memory_comparison(cold, warm).to_csv(tables / "memory_comparison.csv", index=False)
    report_claim_audit(warm).to_csv(tables / "claim_audit.csv", index=False)
    memory.export_json(traces / "memory_export.json")
    memory.close()
    print(memory_comparison(cold, warm).to_string(index=False))
    print(f"Final decision: {warm['evaluations'][-1].decision}")


if __name__ == "__main__":
    main()
