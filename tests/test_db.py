import unittest

from packages.config import Settings
from packages.db.audit import write_audit_log
from packages.db.models import AuditLog, Base
from packages.db.session import build_engine
from packages.model_layer.mock_provider import MockModelProvider
from packages.model_layer.schemas import RISK_DISCLAIMER, ModelRequest
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


if __name__ == "__main__":
    unittest.main()
