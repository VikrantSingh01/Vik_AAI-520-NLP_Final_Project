# FAANG+M Narrative-to-Numbers Research Desk

This repository contains the AAI-520 final team project: an auditable multi-agent
financial research system for Meta, Apple, Amazon, Netflix, Alphabet, and
Microsoft. It compares management narrative, reported financial execution,
recent news, and market confirmation without issuing investment advice.

## Repository Link

https://github.com/VikrantSingh01/Vik_AAI-520-NLP_Final_Project

## Setup

```bash
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m ipykernel install --user \
  --name aai520-final-project \
  --display-name "AAI-520 Final Project (Python 3.12)"
```

Copy `.env.example` to `.env`, then set a descriptive `SEC_USER_AGENT` containing
a real contact address. `FRED_API_KEY` is optional and is not required by the
core implementation.

## Collect and Freeze Data

```bash
.venv/bin/python scripts/collect_snapshot.py
```

The collector caches SEC Company Facts, the latest 10-K/10-Q documents, Yahoo
news metadata, and adjusted prices. It records SHA-256 hashes in
`data/manifest.json`. Do not redistribute complete third-party news articles.

## Run and Validate

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check src tests scripts
.venv/bin/python scripts/evaluate_retrieval.py
.venv/bin/python scripts/evaluate_retrieval.py --minilm
.venv/bin/python scripts/benchmark_models.py
.venv/bin/python scripts/classify_news.py
.venv/bin/python scripts/run_research.py
.venv/bin/jupyter nbconvert --to notebook --execute --inplace \
  notebooks/FAANGM_Narrative_to_Numbers.ipynb \
  --ExecutePreprocessor.kernel_name=aai520-final-project \
  --ExecutePreprocessor.timeout=1800
.venv/bin/python export_report.py
```

`benchmark_models.py` downloads FinBERT and Qwen2.5-1.5B once and measures them
sequentially. On the reference Apple Silicon machine, the first run downloads
approximately 3.5 GB of model weights and takes several minutes. The faster
`classify_news.py` pass then applies cached FinBERT weights to all frozen news.

The research script loads the validated Qwen plan and FinBERT labels, resets
memory, runs the same comparative request cold and warm, and saves tool traces,
claim reconciliation, and memory audits under `outputs/`.

## Deliverable

The executed notebook and professional HTML export live under `notebooks/`.
The notebook displays the required prompt chaining, routing, evaluator-optimizer,
dynamic planning/tool selection, self-reflection, and cross-run memory evidence.

## Responsible Use

This project is educational. Results are descriptive, depend on source quality,
and are not investment advice. See [CITATIONS.md](CITATIONS.md) and
[AI_USE_DISCLOSURE.md](AI_USE_DISCLOSURE.md).
