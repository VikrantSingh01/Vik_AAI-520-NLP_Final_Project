"""Classify every frozen news item with FinBERT."""

from __future__ import annotations

import pandas as pd

from faangm_research.config import Settings
from faangm_research.models import FinBertSentiment, preferred_device
from faangm_research.snapshot import load_snapshot


def main() -> None:
    settings = Settings.default(offline=True)
    _, evidence, _ = load_snapshot(settings.data_dir / "processed")
    news = [item for item in evidence if item.document_type == "news"]
    classifier = FinBertSentiment(device=preferred_device())
    predictions = classifier.predict([item.clean_text for item in news], batch_size=6)
    frame = pd.DataFrame(
        [
            {
                "evidence_id": item.evidence_id,
                "ticker": item.ticker,
                "title": item.title,
                **prediction,
            }
            for item, prediction in zip(news, predictions, strict=True)
        ]
    )
    output = settings.output_dir / "model" / "finbert_sentiment.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    print(frame.groupby(["ticker", "label"]).size().unstack(fill_value=0))
    print(f"Classified {len(frame)} news items on {preferred_device()}")


if __name__ == "__main__":
    main()
