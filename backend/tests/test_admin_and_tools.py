from __future__ import annotations

from app.models import Agent, Conversation, Message, Organization, Tool, User
from app.services.crud import assign_tool_to_agent


def login(client, identifier: str, password: str = "Demo1234!"):
    response = client.post("/api/auth/login", json={"identifier": identifier, "password": password})
    assert response.status_code == 200
    return response


def test_admin_protected(client):
    login(client, "docente")
    response = client.get("/api/admin/users")
    assert response.status_code == 403


def test_admin_delete_tool(client):
    login(client, "admin")
    response = client.delete("/api/admin/tools/1")
    assert response.status_code == 200
    tools = client.get("/api/admin/tools").json()
    assert all(item["id"] != 1 for item in tools)


def test_admin_conversation_list_and_delete(client, db_session_factory):
    session = db_session_factory()
    try:
        admin_user = session.query(User).filter(User.username == "admin").one()
        agent = session.query(Agent).filter(Agent.slug == "alumnos").one()
        conversation = Conversation(
            organization_id=admin_user.organization_id,
            user_id=admin_user.id,
            agent_id=agent.id,
            title="Conversación de prueba",
        )
        session.add(conversation)
        session.flush()
        session.add(
            Message(
                conversation_id=conversation.id,
                role="user",
                content="Hola",
                metadata_={},
            )
        )
        session.commit()
        conversation_id = conversation.id
    finally:
        session.close()

    login(client, "admin")
    response = client.get("/api/admin/conversations")
    assert response.status_code == 200
    conversations = response.json()
    assert any(item["id"] == conversation_id for item in conversations)

    detail = client.get(f"/api/admin/conversations/{conversation_id}/messages")
    assert detail.status_code == 200
    assert detail.json()[0]["content"] == "Hola"

    delete_response = client.delete(f"/api/admin/conversations/{conversation_id}")
    assert delete_response.status_code == 200


def test_admin_archive_conversation_hides_it_from_user_lists(client, db_session_factory):
    session = db_session_factory()
    try:
        admin_user = session.query(User).filter(User.username == "admin").one()
        agent = session.query(Agent).filter(Agent.slug == "alumnos").one()
        conversation = Conversation(
            organization_id=admin_user.organization_id,
            user_id=admin_user.id,
            agent_id=agent.id,
            title="Conversación archivada",
        )
        session.add(conversation)
        session.commit()
        conversation_id = conversation.id
    finally:
        session.close()

    login(client, "admin")
    response = client.patch(f"/api/admin/conversations/{conversation_id}", json={"archived": True})
    assert response.status_code == 200
    assert response.json()["archived"] is True

    conversations = client.get("/api/conversations").json()
    assert all(item["id"] != conversation_id for item in conversations)


def test_tool_execution_allowed(client):
    login(client, "docente")
    response = client.post("/api/chat", json={"agent_id": 1, "message": "Consultá el alumno STU-1001"})
    assert response.status_code == 200
    assert "STU-1001" in response.json()["assistant_message"] or "alumno" in response.json()["assistant_message"].lower()


def test_tool_execution_rejected_when_not_allowed(client, db_session_factory):
    session = db_session_factory()
    try:
        login(client, "admin")
        tool = session.query(Tool).filter(Tool.slug == "get_employee_attendance").one()
        agent = session.query(Agent).filter(Agent.slug == "alumnos").one()
        assign_tool_to_agent(session, agent, tool, permission_level="read")
        session.commit()
    finally:
        session.close()
    response = client.post("/api/chat", json={"agent_id": 1, "message": "Consulta de fichadas de empleados"})
    assert response.status_code == 403


def test_organization_isolation(client, db_session_factory):
    session = db_session_factory()
    try:
        org = Organization(name="Other Org", slug="other-org", active=True)
        session.add(org)
        session.flush()
        other_user = User(
            organization_id=org.id,
            username="external",
            email="external@other.org",
            password_hash="pbkdf2_sha256$1$aa$bb",
            first_name="External",
            last_name="User",
            active=True,
            is_superadmin=False,
        )
        session.add(other_user)
        session.commit()
    finally:
        session.close()
    login(client, "admin")
    response = client.get("/api/admin/users")
    assert response.status_code == 200
    usernames = {item["username"] for item in response.json()}
    assert "admin" in usernames
    assert "external" not in usernames
