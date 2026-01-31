from contextlib import contextmanager
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.api.v1.endpoints import ingestion as ingestion_module
from app.core.config import settings
from app.db.models import ImageSubmission, MedGemmaAnalysis, SubmissionContext
from app.db.session import get_db
from app.main import app
from app.schemas.orchestrator import AgentRunResponse


@contextmanager
def _begin_context(db):
    yield db


def _make_db_session():
    db = MagicMock()
    db.begin.return_value = _begin_context(db)
    return db


def test_ingest_and_run_agentic_persists(sample_image_bytes, tmp_path, monkeypatch):
    db = _make_db_session()
    monkeypatch.setattr(settings, "image_storage_dir", str(tmp_path))
    monkeypatch.setattr(ingestion_module, "store_provenance_manifest", MagicMock())

    def _fake_run(*_args, **_kwargs):
        return MagicMock(
            triage={"primary_findings": "ok"},
            tool_results={"reverse_search": {"status": "ok"}},
            synthesis={"part_2": {"summary": "done"}},
        )

    monkeypatch.setattr(ingestion_module.MedContextAgent, "run", _fake_run)

    response = ingestion_module.ingest_and_run_agentic(
        image_bytes=sample_image_bytes,
        context="testing context",
        context_source="user",
        db=db,
        source_channel="agentic",
        source_url="https://example.com/image.png",
    )

    assert isinstance(response, AgentRunResponse)
    assert response.context_used == "testing context"
    assert response.context_source == "user"

    added_models = [call.args[0] for call in db.add.call_args_list]
    assert any(isinstance(model, ImageSubmission) for model in added_models)
    assert any(isinstance(model, SubmissionContext) for model in added_models)
    assert any(isinstance(model, MedGemmaAnalysis) for model in added_models)
    assert len(list(tmp_path.iterdir())) == 1


def test_orchestrator_run_uses_agentic_ingestion(sample_image_bytes, monkeypatch):
    # Disable demo protection for this test
    monkeypatch.setattr(settings, "demo_access_code", "")

    client = TestClient(app)
    db = _make_db_session()

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db

    expected = AgentRunResponse(
        triage={"primary_findings": "ok"},
        tool_results={},
        synthesis={"part_2": {"summary": "ok"}},
        context_used="ctx",
        context_source="user",
    )

    called = {"value": False}

    def _fake_ingest(*_args, **_kwargs):
        called["value"] = True
        return expected

    monkeypatch.setattr(
        "app.api.v1.endpoints.orchestrator.ingest_and_run_agentic", _fake_ingest
    )

    response = client.post(
        "/api/v1/orchestrator/run",
        files={"file": ("image.png", sample_image_bytes, "image/png")},
        data={"context": "ctx"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert called["value"] is True
    assert response.json()["context_used"] == "ctx"
