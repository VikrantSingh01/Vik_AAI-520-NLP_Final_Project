"""Measure FinBERT sentiment and Qwen structured-planning behavior."""

from __future__ import annotations

import gc
import json
import time

import pandas as pd
import psutil
import torch

from faangm_research.config import Settings
from faangm_research.models import (
    FinBertSentiment,
    QwenStructuredPlanner,
    preferred_device,
    release_model,
)
from faangm_research.snapshot import load_snapshot

QUERIES = [
    "Compare FAANG+M AI narrative, cash flow, news, and market reaction.",
    "Assess Microsoft's AI investment narrative and financial capacity.",
    "Compare META and GOOGL regulatory-news risk.",
    "Review AAPL supply-chain news without market analysis.",
    "Analyze AMZN AWS growth and capital investment.",
    "Assess NFLX advertising catalysts and content risks.",
    "Compare all companies on operating margin and capital intensity.",
    "Find filing evidence about Alphabet antitrust risk.",
    "Summarize recent Meta news sentiment.",
    "Analyze Microsoft market reaction versus QQQ.",
    "Review Apple and Amazon macro sensitivity to rates.",
    "Compare FAANG+M and clearly report unsupported conclusions.",
]


def rss_mb() -> float:
    return psutil.Process().memory_info().rss / (1024**2)


def main() -> None:
    settings = Settings.default(offline=True)
    _, evidence, _ = load_snapshot(settings.data_dir / "processed")
    output = settings.output_dir / "model"
    output.mkdir(parents=True, exist_ok=True)
    device = preferred_device()
    measurements = []

    news = [item for item in evidence if item.document_type == "news"][:12]
    before = rss_mb()
    started = time.perf_counter()
    finbert = FinBertSentiment(device=device)
    load_seconds = time.perf_counter() - started
    inference_started = time.perf_counter()
    sentiments = finbert.predict([item.clean_text for item in news], batch_size=4)
    inference_seconds = time.perf_counter() - inference_started
    after = rss_mb()
    measurements.append(
        {
            "model": finbert.model_name,
            "device": device,
            "load_seconds": load_seconds,
            "inference_seconds": inference_seconds,
            "rss_before_mb": before,
            "rss_after_mb": after,
            "records": len(news),
        }
    )
    pd.DataFrame(
        [
            {
                "evidence_id": item.evidence_id,
                "ticker": item.ticker,
                "title": item.title,
                **sentiment,
            }
            for item, sentiment in zip(news, sentiments, strict=True)
        ]
    ).to_csv(output / "finbert_sentiment.csv", index=False)
    release_model(finbert)
    del finbert
    gc.collect()

    before = rss_mb()
    started = time.perf_counter()
    planner = QwenStructuredPlanner(device=device)
    load_seconds = time.perf_counter() - started
    results = []
    inference_started = time.perf_counter()
    selected_plan = None
    for index, query in enumerate(QUERIES, start=1):
        step_started = time.perf_counter()
        plan, metadata = planner.plan(query)
        elapsed = time.perf_counter() - step_started
        results.append(
            {
                "case": index,
                "query": query,
                "schema_valid": metadata["schema_valid"],
                "fallback_used": metadata["fallback_used"],
                "repair_used": metadata.get("repair_used", False),
                "step_count": len(plan),
                "selected_tools": [step.selected_tool for step in plan],
                "inference_seconds": elapsed,
                "raw": metadata.get("raw", ""),
                "error": metadata.get("error", ""),
            }
        )
        if index == 1:
            selected_plan = plan
    inference_seconds = time.perf_counter() - inference_started
    after = rss_mb()
    measurements.append(
        {
            "model": planner.model_name,
            "device": device,
            "load_seconds": load_seconds,
            "inference_seconds": inference_seconds,
            "rss_before_mb": before,
            "rss_after_mb": after,
            "records": len(QUERIES),
        }
    )
    (output / "qwen_benchmark.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    if selected_plan is not None:
        (output / "validated_qwen_plan.json").write_text(
            json.dumps(
                [step.model_dump(mode="json") for step in selected_plan], indent=2
            ),
            encoding="utf-8",
        )
    release_model(planner)
    del planner
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    pd.DataFrame(measurements).to_csv(output / "model_measurements.csv", index=False)
    print(pd.DataFrame(measurements).to_string(index=False))
    print(
        "Qwen schema-valid rate:",
        sum(item["schema_valid"] for item in results) / len(results),
    )
    print(
        "Qwen fallback rate:",
        sum(item["fallback_used"] for item in results) / len(results),
    )


if __name__ == "__main__":
    main()
