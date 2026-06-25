import unittest

from packages.config import Settings
from packages.db.audit import write_audit_log
from packages.db.models import AuditLog, Base
from packages.db.session import build_engine
from packages.db.stock_scores import get_score_history, write_screening_result
from packages.model_layer.mock_provider import MockModelProvider
from packages.model_layer.schemas import RISK_DISCLAIMER, ModelRequest
from packages.workflow_layer.schemas import ScreeningCandidate, ScreeningResult
from sqlalchemy.orm import Session


def make_sqlite_engine():
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


class SettingsTest(unittest.TestCase):
    def test_settings_default_to_local_sqlite_without_env_file(self) -> None:
        settings = Settings(_env_file=None)

        self.assertTrue(settings.database_url)
        self.assertIsNone(settings.openai_api_key)
        self.assertIsNone(settings.anthropic_api_key)


class AuditLogPersistenceTest(unittest.TestCase):
    def test_audit_log_table_round_trips(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            session.add(
                AuditLog(
                    trace_id="trace-db-001",
                    task_type="stock_analysis",
                    provider="mock",
                    model_name="mock-model-v0",
                    input_summary="Analyze AAPL.",
                    output_summary="Mock response for stock_analysis: Analyze AAPL.",
                    citations=["Yahoo Finance chart API"],
                    token_usage={"input_tokens": 2, "output_tokens": 6, "total_tokens": 8},
                    cost_estimate=0.0,
                    latency_ms=1,
                    risk_disclaimer=RISK_DISCLAIMER,
                )
            )
            session.commit()

        with Session(engine) as session:
            row = session.query(AuditLog).filter_by(trace_id="trace-db-001").one()

        self.assertEqual("stock_analysis", row.task_type)
        self.assertEqual(["Yahoo Finance chart API"], row.citations)
        self.assertEqual(RISK_DISCLAIMER, row.risk_disclaimer)
        self.assertIsNotNone(row.created_at)

    def test_write_audit_log_persists_model_response(self) -> None:
        engine = make_sqlite_engine()
        request = ModelRequest(
            task_type="news_sentiment",
            system_instruction="Summarize sentiment.",
            user_input="Summarize NVDA news.",
            trace_id="trace-db-002",
        )
        response = MockModelProvider().generate(request)

        with Session(engine) as session:
            record = write_audit_log(session, response)
            session.commit()
            record_id = record.id

        with Session(engine) as session:
            row = session.get(AuditLog, record_id)

        self.assertEqual("trace-db-002", row.trace_id)
        self.assertEqual("news_sentiment", row.task_type)
        self.assertIn("Summarize NVDA news.", row.input_summary)
        self.assertEqual(RISK_DISCLAIMER, row.risk_disclaimer)


class StockScorePersistenceTest(unittest.TestCase):
    def _make_result(self, total_score: int = 80) -> ScreeningResult:
        return ScreeningResult(
            market="US",
            requested_limit=5,
            scored_count=1,
            candidates=[
                ScreeningCandidate(
                    rank=1,
                    symbol="AAPL",
                    name="Apple Inc.",
                    sector="Technology",
                    total_score=total_score,
                    recommendation="观察",
                    factors=[{"name": "technical", "score": total_score, "weight": 0.2, "explanation": "test"}],
                    reasons=["区间走势为正，短线动量偏强。"],
                    risks=[],
                    source="test-source",
                    algorithm_version="algorithm-v0.2.2",
                )
            ],
            skipped=[],
            source="test-source",
            generated_at="2026-06-25T13:32:00+00:00",
        )

    def test_write_screening_result_persists_each_candidate(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            records = write_screening_result(session, self._make_result())
            self.assertEqual(1, len(records))
            self.assertEqual("AAPL", records[0].symbol)
            self.assertEqual(80, records[0].total_score)
            session.commit()

    def test_get_score_history_returns_newest_first(self) -> None:
        engine = make_sqlite_engine()

        with Session(engine) as session:
            write_screening_result(session, self._make_result(total_score=60))
            session.commit()
        with Session(engine) as session:
            write_screening_result(session, self._make_result(total_score=85))
            session.commit()

        with Session(engine) as session:
            history = get_score_history(session, "aapl", limit=10)

        self.assertEqual(2, len(history))
        self.assertEqual(85, history[0].total_score)
        self.assertEqual(60, history[1].total_score)


if __name__ == "__main__":
    unittest.main()
