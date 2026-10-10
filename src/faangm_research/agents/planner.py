"""Query-specific planning and dynamic tool selection."""

from __future__ import annotations

from faangm_research.config import COMPANIES
from faangm_research.schemas import PlanStep


def companies_from_query(query: str) -> list[str]:
    lowered = query.lower()
    selected = [
        company.ticker
        for company in COMPANIES
        if company.ticker.lower() in lowered
        or company.name.lower() in lowered
        or any(alias.lower() in lowered for alias in company.aliases)
    ]
    if "faang" in lowered or "all companies" in lowered or not selected:
        return [company.ticker for company in COMPANIES]
    return selected


def build_research_plan(
    query: str,
    memory_records: list[str] | None = None,
) -> list[PlanStep]:
    lowered = query.lower()
    broad = ("compare" in lowered or "faang" in lowered) and "only" not in lowered
    wants_news = broad or any(
        word in lowered for word in ("news", "risk", "narrative", "ai")
    )
    wants_market = broad or any(
        word in lowered for word in ("market", "return", "reaction")
    )
    wants_macro = any(
        word in lowered for word in ("macro", "inflation", "rate", "economy")
    )
    memory_records = memory_records or []
    steps = [
        PlanStep(
            step_id="P1",
            objective="Collect and normalize primary-source financial evidence",
            agent="filing_specialist",
            candidate_tools=["sec_companyfacts", "sec_filing_text", "validated_memory"],
            selected_tool="validated_memory+sec_companyfacts"
            if memory_records
            else "sec_companyfacts",
            success_criteria=(
                "Every displayed metric has a period, concept, accession, and URL"
            ),
            fallback="Use cached SEC snapshot and report non-comparable concepts",
        )
    ]
    if wants_news:
        steps.append(
            PlanStep(
                step_id="P2",
                objective="Run the five-stage news chain",
                agent="news_specialist",
                candidate_tools=["yahoo_news", "news_chain"],
                selected_tool="news_chain",
                dependencies=["P1"],
                success_criteria="Every accepted summary completes all five stages",
                fallback="Use cached metadata and lexical classification",
            )
        )
    if wants_market:
        steps.append(
            PlanStep(
                step_id="P3",
                objective="Measure risk, return, and benchmark-relative confirmation",
                agent="market_specialist",
                candidate_tools=["yahoo_prices", "market_analytics"],
                selected_tool="market_analytics",
                dependencies=["P1"],
                success_criteria="Common-window prices and QQQ benchmark are present",
                fallback="Use frozen price snapshot and disclose missing dates",
            )
        )
    if wants_macro:
        steps.append(
            PlanStep(
                step_id="P4",
                objective="Collect only macro series material to the query",
                agent="macro_specialist",
                candidate_tools=["fred"],
                selected_tool="fred",
                dependencies=["P1"],
                success_criteria="Series IDs, dates, and release context are cited",
                fallback="Emit macro_context_unavailable and continue",
            )
        )
    steps.append(
        PlanStep(
            step_id="P5",
            objective="Synthesize, evaluate, and revise the evidence-linked report",
            agent="supervisor",
            candidate_tools=["synthesizer", "evaluator", "memory"],
            selected_tool="evaluator_optimizer",
            dependencies=[step.step_id for step in steps],
            success_criteria=(
                "No critical unsupported claim and all objectives addressed"
            ),
            fallback="Deliver a marked partial report with failed checks",
        )
    )
    return steps
