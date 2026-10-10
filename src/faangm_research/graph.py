"""Bounded LangGraph orchestration for the investment research agent."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, TypedDict

import pandas as pd
from langgraph.graph import END, START, StateGraph

from faangm_research.agents.evaluator import evaluate_report
from faangm_research.agents.memory import ResearchMemory
from faangm_research.agents.planner import build_research_plan, companies_from_query
from faangm_research.agents.router import route_evidence
from faangm_research.agents.specialists import (
    filing_findings,
    financial_findings,
    market_findings,
    news_findings,
)
from faangm_research.agents.synthesizer import optimize_report, synthesize_report
from faangm_research.analytics.financials import financial_panel
from faangm_research.analytics.market import market_summary
from faangm_research.config import Settings
from faangm_research.schemas import (
    EvidenceItem,
    FinancialFact,
    SourceType,
    ToolEvent,
)
from faangm_research.tools.sec_edgar import CONCEPTS


class GraphState(TypedDict, total=False):
    query: str
    companies: list[str]
    plan: list[Any]
    evidence: list[EvidenceItem]
    facts: list[FinancialFact]
    prices: pd.DataFrame
    routes: list[Any]
    news_stages: list[Any]
    findings: list[Any]
    report: Any
    evaluations: list[Any]
    revision_count: int
    memory_used: list[str]
    fallback_lookups: int
    warnings: list[str]
    run_id: str
    plan_override: list[Any]
    sentiment_overrides: dict[str, str]
    tool_trace: list[ToolEvent]


def metric_memory_usage(
    facts: list[FinancialFact],
    records: list[str],
) -> tuple[list[str], int]:
    mappings = {}
    lessons = []
    for record in records:
        if record.startswith("mapping:"):
            _, ticker, metric, concept = record.split(":", maxsplit=3)
            mappings[(ticker, metric)] = (concept, record)
        elif record.startswith("lesson:"):
            lessons.append(record)
    latest_facts: dict[tuple[str, str], FinancialFact] = {}
    for fact in facts:
        key = (fact.ticker, fact.metric)
        previous = latest_facts.get(key)
        if previous is None or fact.fiscal_year > previous.fiscal_year:
            latest_facts[key] = fact

    used = []
    fallback_lookups = 0
    for key, fact in latest_facts.items():
        saved = mappings.get(key)
        if saved and saved[0] == fact.xbrl_concept:
            used.append(saved[1])
            continue
        candidates = CONCEPTS.get(fact.metric, ())
        if candidates and fact.xbrl_concept != candidates[0]:
            fallback_lookups += 1
    return sorted([*used, *lessons]), fallback_lookups


def prepare_derived_evidence(
    facts: list[FinancialFact],
    prices: pd.DataFrame,
    benchmark: str = "QQQ",
) -> list[EvidenceItem]:
    panel = financial_panel(facts)
    market = market_summary(prices, benchmark=benchmark)
    now = datetime.now(UTC)
    items: list[EvidenceItem] = []
    for row in (
        panel.sort_values("fiscal_year").groupby("ticker").tail(1).to_dict("records")
    ):
        ticker = str(row["ticker"])
        fiscal_year = int(row["fiscal_year"])
        clean = json.dumps(row, default=str, sort_keys=True)
        related = [
            fact
            for fact in facts
            if fact.ticker == ticker and fact.fiscal_year == fiscal_year
        ]
        source_url = str(related[0].source_url)
        items.append(
            EvidenceItem(
                evidence_id=f"FACTS-{ticker}-{fiscal_year}",
                company=related[0].company,
                ticker=ticker,
                source_type=SourceType.DERIVED,
                document_type="financial_summary",
                title=f"{ticker} FY{fiscal_year} normalized financial summary",
                period_end=max(fact.period_end for fact in related),
                url=source_url,
                raw_text_hash=hashlib.sha256(clean.encode()).hexdigest(),
                clean_text=clean,
                retrieved_at=now,
                section="Derived from cited SEC XBRL facts",
            )
        )
    for row in market.to_dict("records"):
        ticker = str(row["ticker"])
        if ticker == benchmark:
            continue
        clean = json.dumps(row, default=str, sort_keys=True)
        items.append(
            EvidenceItem(
                evidence_id=f"MARKET-{ticker}",
                company=ticker,
                ticker=ticker,
                source_type=SourceType.DERIVED,
                document_type="market_summary",
                title=f"{ticker} common-window market summary",
                url=f"https://finance.yahoo.com/quote/{ticker}/history/",
                raw_text_hash=hashlib.sha256(clean.encode()).hexdigest(),
                clean_text=clean,
                retrieved_at=now,
                section=f"Derived from adjusted prices; benchmark={benchmark}",
            )
        )
    return items


def build_research_graph(settings: Settings, memory: ResearchMemory):
    """Compile the agent graph with one bounded evaluator-optimizer loop."""

    def plan_node(state: GraphState) -> dict[str, Any]:
        records = memory.read_records()
        used_memory, fallback_lookups = metric_memory_usage(state["facts"], records)
        companies = companies_from_query(state["query"])
        proposed_plan = state.get("plan_override") or build_research_plan(
            state["query"], records
        )
        return {
            "companies": companies,
            "plan": proposed_plan,
            "memory_used": used_memory,
            "fallback_lookups": fallback_lookups,
            "revision_count": 0,
            "evaluations": [],
            "tool_trace": [],
        }

    def route_node(state: GraphState) -> dict[str, Any]:
        return {"routes": [route_evidence(item) for item in state["evidence"]]}

    def specialist_node(state: GraphState) -> dict[str, Any]:
        started_at = datetime.now(UTC)
        panel = financial_panel(state["facts"])
        market = market_summary(state["prices"], benchmark=settings.benchmark)
        selected_tools = {step.selected_tool for step in state["plan"]}
        findings = financial_findings(panel)
        stages = []
        if "market_analytics" in selected_tools:
            findings += market_findings(market)
        if selected_tools & {"sec_filing_text", "narrative_comparison"}:
            findings += filing_findings(state["evidence"])
        if "news_chain" in selected_tools:
            news, stages = news_findings(
                state["evidence"], state.get("sentiment_overrides", {})
            )
            findings += news
        requested = set(state["companies"])
        completed_at = datetime.now(UTC)
        tool_trace = [
            ToolEvent(
                tool=tool,
                started_at=started_at,
                ended_at=completed_at,
                success=True,
                record_count=(
                    len(stages)
                    if tool == "news_chain"
                    else len(state["facts"])
                    if tool == "sec_companyfacts"
                    else len(market)
                    if tool == "market_analytics"
                    else len(findings)
                ),
                cache_hit=True,
            )
            for tool in sorted(selected_tools - {"evaluator_optimizer"})
        ]
        return {
            "findings": [item for item in findings if item.ticker in requested],
            "news_stages": stages,
            "tool_trace": tool_trace,
        }

    def synthesize_node(state: GraphState) -> dict[str, Any]:
        return {
            "report": synthesize_report(
                state["query"],
                state["findings"],
                settings.as_of_date,
                revision=state["revision_count"],
            )
        }

    def evaluate_node(state: GraphState) -> dict[str, Any]:
        started_at = datetime.now(UTC)
        evidence_registry = {item.evidence_id: item for item in state["evidence"]}
        evaluation = evaluate_report(
            state["report"],
            evidence_registry,
            set(state["companies"]),
        )
        event = ToolEvent(
            tool="evaluator_optimizer",
            started_at=started_at,
            ended_at=datetime.now(UTC),
            success=True,
            record_count=len(state["report"].claims),
            cache_hit=False,
        )
        return {
            "evaluations": [*state["evaluations"], evaluation],
            "tool_trace": [*state["tool_trace"], event],
        }

    def optimize_node(state: GraphState) -> dict[str, Any]:
        evaluation = state["evaluations"][-1]
        return {
            "report": optimize_report(state["report"], evaluation.feedback),
            "revision_count": state["revision_count"] + 1,
        }

    def next_after_evaluation(state: GraphState) -> str:
        evaluation = state["evaluations"][-1]
        if (
            evaluation.decision == "revise"
            and state["revision_count"] < settings.max_revisions
        ):
            return "optimize"
        return "finalize"

    def finalize_node(state: GraphState) -> dict[str, Any]:
        evaluation = state["evaluations"][-1]
        warnings = list(state.get("warnings", []))
        if evaluation.decision == "accept":
            memory.write_accepted_run(
                state["run_id"],
                state["query"],
                state["facts"],
                evaluation,
                state["revision_count"],
            )
        else:
            warnings.append(
                "Evaluator did not accept the bounded run; inspect failed checks."
            )
        completed = [
            step.model_copy(update={"status": "complete"}) for step in state["plan"]
        ]
        return {"plan": completed, "warnings": warnings}

    builder = StateGraph(GraphState)
    builder.add_node("plan", plan_node)
    builder.add_node("route", route_node)
    builder.add_node("specialists", specialist_node)
    builder.add_node("synthesize", synthesize_node)
    builder.add_node("evaluate", evaluate_node)
    builder.add_node("optimize", optimize_node)
    builder.add_node("finalize", finalize_node)
    builder.add_edge(START, "plan")
    builder.add_edge("plan", "route")
    builder.add_edge("route", "specialists")
    builder.add_edge("specialists", "synthesize")
    builder.add_edge("synthesize", "evaluate")
    builder.add_conditional_edges(
        "evaluate",
        next_after_evaluation,
        {"optimize": "optimize", "finalize": "finalize"},
    )
    builder.add_edge("optimize", "evaluate")
    builder.add_edge("finalize", END)
    return builder.compile()


def run_research(
    query: str,
    facts: list[FinancialFact],
    prices: pd.DataFrame,
    source_evidence: list[EvidenceItem],
    settings: Settings,
    memory: ResearchMemory,
    run_label: str,
    plan_override: list[Any] | None = None,
    sentiment_overrides: dict[str, str] | None = None,
) -> GraphState:
    derived = prepare_derived_evidence(facts, prices, settings.benchmark)
    run_id = hashlib.sha256(f"{run_label}:{query}".encode()).hexdigest()[:16]
    graph = build_research_graph(settings, memory)
    initial: GraphState = {
        "query": query,
        "evidence": [*source_evidence, *derived],
        "facts": facts,
        "prices": prices,
        "warnings": [],
        "run_id": run_id,
        "plan_override": plan_override or [],
        "sentiment_overrides": sentiment_overrides or {},
    }
    return graph.invoke(initial, config={"recursion_limit": 20})
