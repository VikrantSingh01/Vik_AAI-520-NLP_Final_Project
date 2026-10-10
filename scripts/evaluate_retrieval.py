"""Evaluate filing retrieval with fixed cross-company questions."""

from __future__ import annotations

import argparse
import time

import pandas as pd

from faangm_research.config import Settings
from faangm_research.snapshot import load_snapshot
from faangm_research.tools.retrieval import FilingRetriever, chunk_evidence

QUESTIONS = [
    (
        "META",
        "How does Meta describe investment in artificial intelligence infrastructure?",
    ),
    ("META", "What risks does Meta identify for advertising and regulation?"),
    ("AAPL", "How does Apple discuss services growth and product competition?"),
    ("AAPL", "What supply chain and component risks does Apple disclose?"),
    ("AMZN", "How does Amazon describe AWS, generative AI, and capital investment?"),
    ("AMZN", "What fulfillment and international operating risks does Amazon report?"),
    ("NFLX", "How does Netflix describe competition for entertainment and engagement?"),
    ("NFLX", "What does Netflix report about advertising and content obligations?"),
    ("GOOGL", "How does Alphabet describe AI investment across Search and Cloud?"),
    ("GOOGL", "What regulatory and antitrust risks does Alphabet disclose?"),
    ("MSFT", "How does Microsoft describe Azure AI and data center investment?"),
    ("MSFT", "What cybersecurity and competition risks does Microsoft report?"),
]


def evaluate(use_minilm: bool) -> tuple[pd.DataFrame, dict[str, float | str]]:
    settings = Settings.default(offline=True)
    _, evidence, _ = load_snapshot(settings.data_dir / "processed")
    chunks = chunk_evidence(evidence)
    started = time.perf_counter()
    retriever = FilingRetriever(chunks, use_minilm=use_minilm)
    build_seconds = time.perf_counter() - started
    records = []
    for expected_ticker, question in QUESTIONS:
        query_started = time.perf_counter()
        results = retriever.search(question, k=5)
        latency = time.perf_counter() - query_started
        tickers = [result.chunk.ticker for result in results]
        first_rank = next(
            (
                rank
                for rank, ticker in enumerate(tickers, start=1)
                if ticker == expected_ticker
            ),
            None,
        )
        records.append(
            {
                "method": retriever.method,
                "expected_ticker": expected_ticker,
                "question": question,
                "first_correct_rank": first_rank,
                "hit_at_1": first_rank == 1,
                "hit_at_3": first_rank is not None and first_rank <= 3,
                "hit_at_5": first_rank is not None and first_rank <= 5,
                "reciprocal_rank": 1 / first_rank if first_rank else 0.0,
                "latency_seconds": latency,
                "top_tickers": ", ".join(tickers),
                "top_excerpt": results[0].chunk.text[:180] if results else "",
            }
        )
    frame = pd.DataFrame(records)
    metrics: dict[str, float | str] = {
        "method": retriever.method,
        "chunks": float(len(chunks)),
        "build_seconds": build_seconds,
        "recall_at_1": float(frame["hit_at_1"].mean()),
        "recall_at_3": float(frame["hit_at_3"].mean()),
        "recall_at_5": float(frame["hit_at_5"].mean()),
        "mrr": float(frame["reciprocal_rank"].mean()),
        "mean_latency_seconds": float(frame["latency_seconds"].mean()),
    }
    return frame, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minilm", action="store_true")
    args = parser.parse_args()
    frame, metrics = evaluate(args.minilm)
    output = Settings.default().output_dir / "tables"
    output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output / f"retrieval_{metrics['method']}_details.csv", index=False)
    pd.DataFrame([metrics]).to_csv(
        output / f"retrieval_{metrics['method']}_metrics.csv", index=False
    )
    print(pd.Series(metrics).to_string())


if __name__ == "__main__":
    main()
