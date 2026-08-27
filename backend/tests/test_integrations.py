from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.models import Agent, Tool
from app.services.llm_providers import get_llm_provider
from app.services.tool_executors import get_executor


class _FakeResponse:
    def __init__(self, data: Any, status_code: int = 200):
        self._data = data
        self.status_code = status_code
        self.text = str(data)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> Any:
        return self._data


class _FakeClient:
    last_request: dict[str, Any] | None = None
    next_response: _FakeResponse = _FakeResponse({})

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, json=None, headers=None):
        type(self).last_request = {"url": url, "json": json, "headers": headers}
        return type(self).next_response


def login(client, identifier: str, password: str = "Demo1234!"):
    response = client.post("/api/auth/login", json={"identifier": identifier, "password": password})
    assert response.status_code == 200


def test_get_student_uses_n8n_webhook_when_configured(client, db_session_factory, monkeypatch):
    _FakeClient.last_request = None
    session = db_session_factory()
    try:
        tool = session.query(Tool).filter(Tool.slug == "get_student").one()
        tool.configuration = {
            "webhook_url": "https://n8n.example/webhook/get-student",
            "timeout_seconds": 5,
        }
        session.commit()
    finally:
        session.close()

    monkeypatch.setattr("app.services.tool_executors.httpx.Client", _FakeClient)
    _FakeClient.next_response = _FakeResponse(
        {
            "student": {
                "student_id": "STU-1001",
                "name": "Camila Herrera",
                "status": "active",
            },
            "source": "n8n",
        }
    )

    login(client, "docente")
    response = client.post("/api/chat", json={"agent_id": 1, "message": "Consultá el alumno STU-1001"})
    assert response.status_code == 200
    body = response.json()["assistant_message"]
    assert "STU-1001" in body
    assert "Camila Herrera" in body
    assert _FakeClient.last_request is not None
    assert _FakeClient.last_request["url"] == "https://n8n.example/webhook/get-student"
    assert _FakeClient.last_request["json"]["tool_slug"] == "get_student"


def test_rest_agent_provider_is_used_for_rest_agents(client, db_session_factory, monkeypatch):
    _FakeClient.last_request = None
    get_settings.cache_clear()
    monkeypatch.setenv("EXTERNAL_AGENT_REST_URL", "https://agent.example/rest")
    monkeypatch.setenv("EXTERNAL_AGENT_REST_API_KEY", "secret-rest")
    monkeypatch.setattr("app.services.llm_providers.httpx.Client", _FakeClient)
    _FakeClient.next_response = _FakeResponse(
        {
            "content": "Respuesta desde el agente REST",
            "tool_calls": [],
        }
    )

    session = db_session_factory()
    try:
        agent_id = session.query(Agent).filter(Agent.slug == "externo-rest").one().id
    finally:
        session.close()

    login(client, "admin")
    response = client.post("/api/chat", json={"agent_id": agent_id, "message": "Hola desde REST"})
    assert response.status_code == 200
    assert "Respuesta desde el agente REST" in response.json()["assistant_message"] or "Respuesta desde el agente REST" in response.text
    assert _FakeClient.last_request is not None
    assert _FakeClient.last_request["url"] == "https://agent.example/rest"
    assert _FakeClient.last_request["json"]["provider"] == "rest"


def test_mcp_agent_provider_is_used_for_mcp_agents(client, db_session_factory, monkeypatch):
    _FakeClient.last_request = None
    get_settings.cache_clear()
    monkeypatch.setenv("EXTERNAL_AGENT_MCP_URL", "https://agent.example/mcp")
    monkeypatch.setenv("EXTERNAL_AGENT_MCP_API_KEY", "secret-mcp")
    monkeypatch.setattr("app.services.llm_providers.httpx.Client", _FakeClient)
    _FakeClient.next_response = _FakeResponse(
        {
            "jsonrpc": "2.0",
            "result": {
                "content": "Respuesta desde MCP",
                "tool_calls": [],
            },
        }
    )

    session = db_session_factory()
    try:
        agent_id = session.query(Agent).filter(Agent.slug == "externo-mcp").one().id
    finally:
        session.close()

    login(client, "admin")
    response = client.post("/api/chat", json={"agent_id": agent_id, "message": "Hola desde MCP"})
    assert response.status_code == 200
    assert "Respuesta desde MCP" in response.json()["assistant_message"] or "Respuesta desde MCP" in response.text
    assert _FakeClient.last_request is not None
    assert _FakeClient.last_request["url"] == "https://agent.example/mcp"
    assert _FakeClient.last_request["json"]["method"] == "agent.generate"
