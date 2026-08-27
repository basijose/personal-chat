from __future__ import annotations


def login(client, identifier: str, password: str = "Demo1234!"):
    response = client.post("/api/auth/login", json={"identifier": identifier, "password": password})
    assert response.status_code == 200
    return response


def test_conversation_and_messages(client):
    login(client, "docente")
    response = client.post("/api/chat", json={"agent_id": 1, "message": "Necesito información del alumno STU-1001"})
    assert response.status_code == 200
    conversation_id = response.json()["conversation_id"]
    messages = client.get(f"/api/conversations/{conversation_id}/messages")
    assert messages.status_code == 200
    assert len(messages.json()) >= 2

