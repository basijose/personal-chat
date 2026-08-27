from __future__ import annotations


def login(client, identifier: str, password: str = "Demo1234!"):
    response = client.post("/api/auth/login", json={"identifier": identifier, "password": password})
    assert response.status_code == 200
    return response


def test_list_agents_by_permissions(client):
    login(client, "docente")
    response = client.get("/api/agents")
    assert response.status_code == 200
    slugs = {agent["slug"] for agent in response.json()}
    assert slugs == {"alumnos", "presentismo-alumnos"}


def test_agent_access_denied(client):
    login(client, "rrhh")
    response = client.get("/api/agents")
    assert response.status_code == 200
    slugs = {agent["slug"] for agent in response.json()}
    assert slugs == {"presentismo-empleados"}
    denied = client.post("/api/chat", json={"agent_id": 1, "message": "Necesito alumnos"})
    assert denied.status_code in {403, 404}

