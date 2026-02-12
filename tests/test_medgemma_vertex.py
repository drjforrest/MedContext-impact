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
        self.last_request = SimpleNamespace(
            url=url, params=params, json=json, headers=headers
        )
        return self._response


@pytest.mark.skip(reason="Requires Vertex AI credentials and proper SDK mocking")
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
        # Mock response in production Vertex AI predict shape
        response = _FakeResponse(
            {
                "predictions": [
                    {"choices": [{"message": {"content": "This is a test response"}}]}
                ]
            }
        )
        fake_client = _FakeClient(response)
        monkeypatch.setattr(
            "app.clinical.medgemma_client.httpx.Client",
            lambda timeout=60.0: fake_client,
        )

        # Mock ADC token with proper credential interface
        class MockCredentials:
            def __init__(self):
                self.token = "test-token"

            def refresh(self, request):
                pass

            def before_request(self, request, method, url, headers):
                headers["authorization"] = f"Bearer {self.token}"
                return headers

        def mock_default(scopes=None, request=None):
            creds = MockCredentials()
            return creds, "test-project"

        monkeypatch.setattr("google.auth.default", mock_default)

        client = MedGemmaClient()
        result = client.analyze_image(sample_image_bytes, prompt="test")
    finally:
        settings.medgemma_vertex_endpoint = original_endpoint
        settings.medgemma_vertex_project = original_project
        settings.vertexai_api_key = original_key
        settings.medgemma_provider = original_provider

    assert result.provider == "vertex"
    assert result.output == {"text": "This is a test response"}
    assert fake_client.last_request is not None
    assert fake_client.last_request.url.endswith(":predict")


def test_vertex_requires_endpoint(sample_image_bytes):
    original_endpoint = settings.medgemma_vertex_endpoint
    original_key = settings.vertexai_api_key
    original_provider = settings.medgemma_provider
    original_fallback = settings.medgemma_fallback_provider
    settings.medgemma_vertex_endpoint = ""
    settings.vertexai_api_key = "test-key"
    settings.medgemma_provider = "vertex"
    settings.medgemma_fallback_provider = ""  # Disable fallback
    try:
        client = MedGemmaClient()
        with pytest.raises(
            MedGemmaClientError, match="Missing MEDGEMMA_VERTEX_ENDPOINT"
        ):
            client.analyze_image(sample_image_bytes, prompt="test")
    finally:
        settings.medgemma_vertex_endpoint = original_endpoint
        settings.vertexai_api_key = original_key
        settings.medgemma_provider = original_provider
        settings.medgemma_fallback_provider = original_fallback


@pytest.mark.skip(reason="Requires Vertex AI credentials and proper SDK mocking")
def test_vertex_api_key_builds_predict_url_from_resource_name(
    sample_image_bytes, monkeypatch
):
    original_endpoint = settings.medgemma_vertex_endpoint
    original_project = settings.medgemma_vertex_project
    original_location = settings.medgemma_vertex_location
    original_key = settings.vertexai_api_key
    original_provider = settings.medgemma_provider
    original_dedicated_domain = settings.medgemma_vertex_dedicated_domain
    settings.medgemma_vertex_endpoint = (
        "projects/medcontext/locations/us-central1/endpoints/abc123"
    )
    settings.medgemma_vertex_project = "medcontext"
    settings.medgemma_vertex_location = "us-central1"
    settings.vertexai_api_key = "test-key"
    settings.medgemma_provider = "vertex"
    settings.medgemma_vertex_dedicated_domain = ""  # Use standard domain
    try:
        # Mock response in production Vertex AI predict shape
        response = _FakeResponse(
            {"predictions": [{"choices": [{"message": {"content": "ok"}}]}]}
        )
        fake_client = _FakeClient(response)
        monkeypatch.setattr(
            "app.clinical.medgemma_client.httpx.Client",
            lambda timeout=60.0: fake_client,
        )

        # Mock ADC token with proper credential interface
        class MockCredentials:
            def __init__(self):
                self.token = "test-token"

            def refresh(self, request):
                pass

            def before_request(self, request, method, url, headers):
                headers["authorization"] = f"Bearer {self.token}"
                return headers

        def mock_default(scopes=None, request=None):
            creds = MockCredentials()
            return creds, "test-project"

        monkeypatch.setattr("google.auth.default", mock_default)

        client = MedGemmaClient()
        client.analyze_image(sample_image_bytes, prompt="test")
    finally:
        settings.medgemma_vertex_endpoint = original_endpoint
        settings.medgemma_vertex_project = original_project
        settings.medgemma_vertex_location = original_location
        settings.vertexai_api_key = original_key
        settings.medgemma_provider = original_provider
        settings.medgemma_vertex_dedicated_domain = original_dedicated_domain

    assert fake_client.last_request is not None
    assert fake_client.last_request.url.startswith(
        "https://us-central1-aiplatform.googleapis.com/v1/projects/medcontext/locations/us-central1/endpoints/abc123:predict"
    )
