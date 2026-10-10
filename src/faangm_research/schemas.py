"""Validated data contracts shared across tools and agents."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class SourceType(StrEnum):
    SEC = "sec"
    YAHOO = "yahoo"
    FRED = "fred"
    DERIVED = "derived"


class Route(StrEnum):
    FILING = "filing"
    NEWS = "news"
    MARKET = "market"
    MACRO = "macro"
    MIXED = "mixed"


class ToolEvent(StrictModel):
    tool: str
    started_at: datetime
    ended_at: datetime
    success: bool
    record_count: int = 0
    cache_hit: bool = False
    retry_count: int = 0
    evidence_ids: list[str] = Field(default_factory=list)
    error: str | None = None


class EvidenceItem(StrictModel):
    evidence_id: str
    company: str
    ticker: str
    source_type: SourceType
    document_type: str
    title: str
    published_at: datetime | None = None
    period_end: date | None = None
    filing_date: date | None = None
    accession_number: str | None = None
    url: HttpUrl
    raw_text_hash: str
    clean_text: str
    retrieved_at: datetime
    section: str | None = None


class FinancialFact(StrictModel):
    company: str
    ticker: str
    metric: str
    value: float
    unit: str
    period_start: date | None = None
    period_end: date
    fiscal_year: int
    fiscal_period: str
    form: str
    filed_at: date
    accession_number: str
    xbrl_concept: str
    is_derived: bool = False
    source_url: HttpUrl


class PlanStep(StrictModel):
    step_id: str
    objective: str
    agent: str
    candidate_tools: list[str]
    selected_tool: str
    dependencies: list[str] = Field(default_factory=list)
    success_criteria: str
    fallback: str
    status: Literal["pending", "running", "complete", "failed", "skipped"] = "pending"


class RouteDecision(StrictModel):
    item_id: str
    route: Route
    secondary_route: Route | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    required_tools: list[str] = Field(default_factory=list)
    used_fallback: bool = False


class Finding(StrictModel):
    finding_id: str
    ticker: str
    category: str
    claim: str
    direction: Literal["positive", "negative", "neutral", "mixed"]
    evidence_ids: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)


class NewsStageResult(StrictModel):
    evidence_id: str
    stage: Literal["ingest", "preprocess", "classify", "extract", "summarize"]
    passed_gate: bool
    payload: dict[str, Any]
    message: str


class ReportClaim(StrictModel):
    claim_id: str
    text: str
    evidence_ids: list[str] = Field(min_length=1)
    numeric_values: list[float] = Field(default_factory=list)


class ResearchReport(StrictModel):
    title: str
    as_of_date: date
    executive_summary: str
    claims: list[ReportClaim]
    catalysts: list[str]
    risks: list[str]
    divergences: list[str]
    unknowns: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    disclaimer: str
    revision: int = 0


class EvaluationResult(StrictModel):
    decision: Literal["accept", "revise", "request_evidence"]
    total_score: float = Field(ge=0.0, le=100.0)
    citation_coverage: float = Field(ge=0.0, le=1.0)
    numeric_consistency: float = Field(ge=0.0, le=1.0)
    groundedness: float = Field(ge=0.0, le=1.0)
    analytical_balance: float = Field(ge=0.0, le=1.0)
    freshness: float = Field(ge=0.0, le=1.0)
    question_coverage: float = Field(ge=0.0, le=1.0)
    style_uncertainty: float = Field(ge=0.0, le=1.0)
    critical_issues: list[str] = Field(default_factory=list)
    feedback: list[str] = Field(default_factory=list)


class ResearchState(StrictModel):
    query: str
    companies: list[str]
    as_of_date: date
    research_plan: list[PlanStep] = Field(default_factory=list)
    completed_steps: list[str] = Field(default_factory=list)
    tool_trace: list[ToolEvent] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    metrics: list[FinancialFact] = Field(default_factory=list)
    routes: list[RouteDecision] = Field(default_factory=list)
    specialist_findings: list[Finding] = Field(default_factory=list)
    draft_report: ResearchReport | None = None
    evaluation: EvaluationResult | None = None
    revision_count: int = 0
    memory_used: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
