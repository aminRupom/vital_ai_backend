from httpx import AsyncClient


async def test_register_then_login(client: AsyncClient):
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User",
            "role": "front_desk",
        },
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == "newuser@example.com"

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "newuser@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    assert token

    me_response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "newuser@example.com"


async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "User",
            "role": "front_desk",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "email": "dupe@example.com",
        "password": "password123",
        "full_name": "Dupe",
        "role": "front_desk",
    }
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


async def test_protected_endpoint_requires_token(client: AsyncClient):
    response = await client.post(
        "/api/v1/intake",
        json={
            "patient_name": "x",
            "contact_reason": "y",
            "contact_channel": "phone",
        },
    )
    assert response.status_code == 401
