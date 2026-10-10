"""Validated cross-run memory backed by SQLite."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from faangm_research.schemas import EvaluationResult, FinancialFact


class ResearchMemory:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS metric_mappings (
                ticker TEXT NOT NULL,
                metric TEXT NOT NULL,
                concept TEXT NOT NULL,
                validated_at TEXT NOT NULL,
                PRIMARY KEY (ticker, metric)
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluation_lessons (
                lesson TEXT PRIMARY KEY,
                count INTEGER NOT NULL,
                last_used_at TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS run_history (
                run_id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                quality_score REAL NOT NULL,
                revisions INTEGER NOT NULL,
                accepted INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def reset(self) -> None:
        for table in ("metric_mappings", "evaluation_lessons", "run_history"):
            self.connection.execute(f"DELETE FROM {table}")
        self.connection.commit()

    def read_records(self) -> list[str]:
        mappings = self.connection.execute(
            "SELECT ticker, metric, concept FROM metric_mappings "
            "ORDER BY ticker, metric"
        ).fetchall()
        lessons = self.connection.execute(
            "SELECT lesson FROM evaluation_lessons ORDER BY lesson"
        ).fetchall()
        return [
            f"mapping:{ticker}:{metric}:{concept}"
            for ticker, metric, concept in mappings
        ] + [f"lesson:{lesson[0]}" for lesson in lessons]

    def write_accepted_run(
        self,
        run_id: str,
        query: str,
        facts: list[FinancialFact],
        evaluation: EvaluationResult,
        revisions: int,
    ) -> None:
        if evaluation.decision != "accept":
            raise ValueError("Only accepted runs may update durable memory")
        now = datetime.now(UTC).isoformat()
        latest_facts: dict[tuple[str, str], FinancialFact] = {}
        for fact in facts:
            key = (fact.ticker, fact.metric)
            previous = latest_facts.get(key)
            if previous is None or fact.fiscal_year > previous.fiscal_year:
                latest_facts[key] = fact
        for fact in latest_facts.values():
            self.connection.execute(
                """
                INSERT INTO metric_mappings(ticker, metric, concept, validated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(ticker, metric) DO UPDATE SET
                    concept=excluded.concept,
                    validated_at=excluded.validated_at
                """,
                (fact.ticker, fact.metric, fact.xbrl_concept, now),
            )
        for lesson in evaluation.feedback or [
            "Preserve citations and calibrated uncertainty"
        ]:
            self.connection.execute(
                """
                INSERT INTO evaluation_lessons(lesson, count, last_used_at)
                VALUES (?, 1, ?)
                ON CONFLICT(lesson) DO UPDATE SET
                    count=count + 1,
                    last_used_at=excluded.last_used_at
                """,
                (lesson, now),
            )
        self.connection.execute(
            """
            INSERT OR REPLACE INTO run_history
            (run_id, query, quality_score, revisions, accepted, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (run_id, query, evaluation.total_score, revisions, now),
        )
        self.connection.commit()

    def export_json(self, path: Path) -> None:
        records = {
            "memory_records": self.read_records(),
            "run_history": self.connection.execute(
                "SELECT run_id, query, quality_score, revisions, accepted, created_at "
                "FROM run_history ORDER BY created_at"
            ).fetchall(),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    def close(self) -> None:
        self.connection.close()
