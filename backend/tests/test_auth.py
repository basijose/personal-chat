from __future__ import annotations


def test_login_success(client):
    response = client.post("/api/auth/login", json={"identifier": "admin", "password": "Demo1234!"})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["username"] == "admin"
    assert response.cookies.get("personal_chat_access_token")


def test_login_invalid(client):
    response = client.post("/api/auth/login", json={"identifier": "admin", "password": "wrong"})
    assert response.status_code == 401

