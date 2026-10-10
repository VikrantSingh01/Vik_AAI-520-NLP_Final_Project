from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from faangm_research.agents.evaluator import evaluate_report
from faangm_research.agents.memory import ResearchMemory
from faangm_research.agents.planner import build_research_plan, companies_from_query
from faangm_research.agents.router import route_evidence
from faangm_research.agents.synthesizer import optimize_report, synthesize_report
from faangm_research.analytics.financials import financial_panel
from faangm_research.graph import metric_memory_usage
from faangm_research.models import parse_plan_json
from faangm_research.schemas import (
    EvidenceItem,
    FinancialFact,
    Finding,
    ReportClaim,
    ResearchReport,
    SourceType,
)
from faangm_research.tools.retrieval import FilingRetriever, chunk_evidence
from faangm_research.workflows.news_chain import run_news_chain

NOW = datetime(2026, 9, 7, tzinfo=UTC)


def evidence(document_type: str = "news") -> EvidenceItem:
    return EvidenceItem(
        evidence_id="NEWS-MSFT-1",
        company="Microsoft",
        ticker="MSFT",
        source_type=SourceType.YAHOO if document_type == "news" else SourceType.SEC,
        document_type=document_type,
        title="Microsoft reports strong AI cloud revenue growth of 15%",
        url="https://example.com/source",
        raw_text_hash="a" * 64,
        clean_text="Microsoft reports strong AI cloud revenue growth of 15%.",
        retrieved_at=NOW,
    )


def fact(metric: str, value: float, year: int) -> FinancialFact:
    return FinancialFact(
        company="Microsoft",
        ticker="MSFT",
        metric=metric,
        value=value,
        unit="USD",
        period_start=date(year - 1, 7, 1),
        period_end=date(year, 6, 30),
        fiscal_year=year,
        fiscal_period="FY",
        form="10-K",
        filed_at=date(year, 7, 30),
        accession_number=f"000-test-{year}",
        xbrl_concept=metric,
        source_url="https://www.sec.gov/example",
    )


def test_news_chain_has_all_five_passing_stages() -> None:
    stages, finding = run_news_chain(evidence())
    assert [stage.stage for stage in stages] == [
        "ingest",
        "preprocess",
        "classify",
        "extract",
        "summarize",
    ]
    assert all(stage.passed_gate for stage in stages)
    assert finding and finding.evidence_ids == ["NEWS-MSFT-1"]


def test_news_chain_accepts_finbert_sentiment_override() -> None:
    stages, finding = run_news_chain(evidence(), sentiment_override="negative")
    classification = next(stage for stage in stages if stage.stage == "classify")
    assert classification.payload["sentiment_method"] == "FinBERT"
    assert finding and finding.direction == "negative"


def test_query_plan_omits_unrequested_market_tool() -> None:
    plan = build_research_plan("Compare META and GOOGL regulatory-news risk only")
    assert "market_analytics" not in {step.selected_tool for step in plan}


def test_planner_is_query_specific() -> None:
    plan = build_research_plan("Assess MSFT regulatory news risk")
    selected = {step.selected_tool for step in plan}
    assert "news_chain" in selected
    assert "market_analytics" not in selected
    assert "fred" not in selected
    assert companies_from_query("Assess Microsoft") == ["MSFT"]


def test_router_selects_news_and_filing_specialists() -> None:
    assert route_evidence(evidence()).route.value == "news"
    assert route_evidence(evidence("10-K")).route.value == "filing"


def test_financial_panel_calculates_transparent_metrics() -> None:
    facts = []
    for year, scale in ((2024, 1.0), (2025, 1.1)):
        facts.extend(
            [
                fact("revenue", 100 * scale, year),
                fact("operating_income", 25 * scale, year),
                fact("operating_cash_flow", 30 * scale, year),
                fact("capital_expenditures", 10 * scale, year),
            ]
        )
    panel = financial_panel(facts)
    latest = panel.sort_values("fiscal_year").iloc[-1]
    assert latest["revenue_growth"] == pytest.approx(0.1)
    assert latest["operating_margin"] == pytest.approx(0.25)
    assert latest["fcf_margin"] == pytest.approx(0.2)


def test_sec_concepts_include_productive_assets_fallback() -> None:
    from faangm_research.tools.sec_edgar import CONCEPTS

    assert CONCEPTS["capital_expenditures"] == (
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    )


def test_evaluator_requires_and_accepts_revision() -> None:
    finding = Finding(
        finding_id="F1",
        ticker="MSFT",
        category="news",
        claim="MSFT has source-supported evidence.",
        direction="positive",
        evidence_ids=["NEWS-MSFT-1"],
        confidence=0.9,
    )
    report = synthesize_report("Assess MSFT", [finding], date(2026, 9, 7))
    first = evaluate_report(report, {"NEWS-MSFT-1"}, {"MSFT"})
    assert first.decision == "revise"
    revised = optimize_report(report, first.feedback)
    second = evaluate_report(revised, {"NEWS-MSFT-1"}, {"MSFT"})
    assert second.decision == "accept"


def test_evaluator_rejects_number_not_in_cited_evidence() -> None:
    source = evidence().model_copy(
        update={"clean_text": '{"total_return": 0.123, "ticker": "MSFT"}'}
    )
    report = ResearchReport(
        title="Audit",
        as_of_date=date(2026, 9, 7),
        executive_summary="Numeric audit",
        claims=[
            ReportClaim(
                claim_id="C1",
                text="MSFT returned 99.9%.",
                evidence_ids=[source.evidence_id],
            )
        ],
        catalysts=["Supported catalyst"],
        risks=["Supported risk"],
        divergences=[],
        unknowns=[],
        confidence=0.5,
        disclaimer="This is not investment advice.",
        revision=1,
    )
    result = evaluate_report(report, {source.evidence_id: source}, {"MSFT"})
    assert result.numeric_consistency == 0.0
    assert result.decision == "request_evidence"


def test_memory_only_writes_accepted_runs(tmp_path: Path) -> None:
    memory = ResearchMemory(tmp_path / "memory.sqlite")
    finding = Finding(
        finding_id="F1",
        ticker="MSFT",
        category="news",
        claim="MSFT evidence.",
        direction="positive",
        evidence_ids=["NEWS-MSFT-1"],
        confidence=0.9,
    )
    report = synthesize_report("MSFT", [finding], date(2026, 9, 7), revision=1)
    accepted = evaluate_report(report, {"NEWS-MSFT-1"}, {"MSFT"})
    memory.write_accepted_run(
        "run-1", "MSFT", [fact("revenue", 100, 2025)], accepted, 1
    )
    assert memory.read_records()
    memory.close()


def test_metric_memory_eliminates_real_concept_fallback() -> None:
    latest = fact("capital_expenditures", 100, 2025).model_copy(
        update={"xbrl_concept": "PaymentsToAcquireProductiveAssets"}
    )
    cold_used, cold_fallbacks = metric_memory_usage([latest], [])
    record = (
        "mapping:MSFT:capital_expenditures:PaymentsToAcquireProductiveAssets"
    )
    warm_used, warm_fallbacks = metric_memory_usage([latest], [record])
    assert not cold_used and cold_fallbacks == 1
    assert warm_used == [record] and warm_fallbacks == 0


def test_filing_retriever_returns_traceable_chunks() -> None:
    filing = evidence("10-K").model_copy(
        update={
            "clean_text": (
                "Microsoft Azure artificial intelligence cloud growth. "
                "Cybersecurity and competition are material risks."
            )
        }
    )
    chunks = chunk_evidence([filing], chunk_size=70, overlap=10)
    results = FilingRetriever(chunks).search("Azure AI cloud", k=1)
    assert results[0].chunk.evidence_id == filing.evidence_id
    assert results[0].score > 0


def test_qwen_plan_parser_validates_structured_json() -> None:
    plan = build_research_plan("Assess MSFT news risk")
    payload = [step.model_dump_json() for step in plan]
    parsed = parse_plan_json("[" + ",".join(payload) + "]")
    assert parsed[-1].selected_tool == "evaluator_optimizer"
