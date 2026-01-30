from types import SimpleNamespace

import pytest

from app.clinical.medgemma_client import MedGemmaClient, MedGemmaClientError
from app.core.config import settings


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.text = "ok"

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, response):
        self._response = response
        self.last_request = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, params=None, json=None, headers=None):
        self.last_request = SimpleNamespace(url=url, params=params, json=json, headers=headers)
        return self._response


def test_vertex_api_key_uses_predict_endpoint(sample_image_bytes, monkeypatch):
    original_endpoint = settings.medgemma_vertex_endpoint
    original_project = settings.medgemma_vertex_project
    original_key = settings.vertexai_api_key
    original_provider = settings.medgemma_provider
    settings.medgemma_vertex_endpoint = "https://us-central1-aiplatform.googleapis.com/v1/projects/p/locations/us-central1/endpoints/123"
    settings.medgemma_vertex_project = ""
    settings.vertexai_api_key = "test-key"
    settings.medgemma_provider = "vertexai"
    try:
        response = _FakeResponse({"predictions": [{"text": "ok"}]})
        fake_client = _FakeClient(response)
        monkeypatch.setattr(
            "app.clinical.medgemma_client.httpx.Client",
            lambda timeout=60.0: fake_client,
        )
        client = MedGemmaClient()
        result = client.analyze_image(sample_image_bytes, prompt="test")
    finally:
        settings.medgemma_vertex_endpoint = original_endpoint
        settings.medgemma_vertex_project = original_project
        settings.vertexai_api_key = original_key
        settings.medgemma_provider = original_provider

    assert result.provider == "vertex"
    assert result.output == [{"text": "ok"}]
    assert fake_client.last_request is not None
    assert fake_client.last_request.url.endswith(":predict")
    assert fake_client.last_request.params == {"key": "test-key"}


def test_vertex_requires_endpoint(sample_image_bytes):
    original_endpoint = settings.medgemma_vertex_endpoint
    original_key = settings.vertexai_api_key
    original_provider = settings.medgemma_provider
    settings.medgemma_vertex_endpoint = ""
    settings.vertexai_api_key = "test-key"
    settings.medgemma_provider = "vertex"
    try:
        client = MedGemmaClient()
        with pytest.raises(MedGemmaClientError):
            client.analyze_image(sample_image_bytes, prompt="test")
    finally:
        settings.medgemma_vertex_endpoint = original_endpoint
        settings.vertexai_api_key = original_key
        settings.medgemma_provider = original_provider


def test_vertex_api_key_builds_predict_url_from_resource_name(
    sample_image_bytes, monkeypatch
):
    original_endpoint = settings.medgemma_vertex_endpoint
    original_project = settings.medgemma_vertex_project
    original_location = settings.medgemma_vertex_location
    original_key = settings.vertexai_api_key
    original_provider = settings.medgemma_provider
    settings.medgemma_vertex_endpoint = (
        "projects/medcontext/locations/us-central1/endpoints/abc123"
    )
    settings.medgemma_vertex_project = "medcontext"
    settings.medgemma_vertex_location = "us-central1"
    settings.vertexai_api_key = "test-key"
    settings.medgemma_provider = "vertex"
    try:
        response = _FakeResponse({"predictions": [{"text": "ok"}]})
        fake_client = _FakeClient(response)
        monkeypatch.setattr(
            "app.clinical.medgemma_client.httpx.Client",
            lambda timeout=60.0: fake_client,
        )
        client = MedGemmaClient()
        client.analyze_image(sample_image_bytes, prompt="test")
    finally:
        settings.medgemma_vertex_endpoint = original_endpoint
        settings.medgemma_vertex_project = original_project
        settings.medgemma_vertex_location = original_location
        settings.vertexai_api_key = original_key
        settings.medgemma_provider = original_provider

    assert fake_client.last_request is not None
    assert fake_client.last_request.url.startswith(
        "https://us-central1-aiplatform.googleapis.com/v1/projects/medcontext/locations/us-central1/endpoints/abc123:predict"
    )
