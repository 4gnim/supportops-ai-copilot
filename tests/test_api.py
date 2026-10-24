from fastapi.testclient import TestClient

from supportops.api import app, get_rag_service


class FakeRAGService:
    def answer(self, query: str) -> dict:
        return {
            "answer": f"Jawaban simulasi untuk: {query}",
            "sources": [
                {
                    "source": "incident_response.md",
                    "chunk_id": "incident_response::chunk-000",
                    "excerpt": "Periksa status layanan.",
                    "distance": 0.12,
                }
            ],
        }


def test_health_does_not_require_api_key() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "X-Request-ID" in response.headers


def test_ask_rejects_missing_api_key() -> None:
    client = TestClient(app)
    response = client.post("/ask", json={"query": "Apa itu SEV-1?"})
    assert response.status_code == 401


def test_ask_returns_sources_and_request_id() -> None:
    app.dependency_overrides[get_rag_service] = lambda: FakeRAGService()
    try:
        client = TestClient(app)
        response = client.post(
            "/ask",
            headers={"X-API-Key": "change-me-local-only"},
            json={"query": "Apa yang perlu dilakukan saat insiden?"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "request_id" in body
        assert "Jawaban simulasi" in body["answer"]
        assert body["sources"][0]["source"] == "incident_response.md"
    finally:
        app.dependency_overrides.clear()


def test_ask_validates_query_length() -> None:
    client = TestClient(app)
    response = client.post(
        "/ask",
        headers={"X-API-Key": "change-me-local-only"},
        json={"query": "a"},
    )
    assert response.status_code == 422
