from httpx import AsyncClient


async def test_create_intake(client: AsyncClient, admin_headers: dict):
    response = await client.post(
        "/api/v1/intake",
        json={
            "patient_name": "Jane Synthetic",
            "contact_reason": "Booking appointment",
            "contact_channel": "phone",
            "notes": "Prefers morning slot",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "intake_received"
    assert body["patient_name"] == "Jane Synthetic"
    assert "id" in body


async def test_get_intake(client: AsyncClient, admin_headers: dict):
    create = await client.post(
        "/api/v1/intake",
        json={
            "patient_name": "John Synthetic",
            "contact_reason": "Test result enquiry",
            "contact_channel": "email",
        },
        headers=admin_headers,
    )
    case_id = create.json()["id"]

    response = await client.get(f"/api/v1/intake/{case_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["id"] == case_id


async def test_status_update_blocked_for_front_desk(
    client: AsyncClient, admin_headers: dict, front_desk_headers: dict
):
    create = await client.post(
        "/api/v1/intake",
        json={
            "patient_name": "x",
            "contact_reason": "y",
            "contact_channel": "phone",
        },
        headers=admin_headers,
    )
    case_id = create.json()["id"]

    response = await client.patch(
        f"/api/v1/intake/{case_id}/status",
        json={"status": "consent_pending"},
        headers=front_desk_headers,
    )
    assert response.status_code == 403


async def test_status_update_allowed_for_admin(client: AsyncClient, admin_headers: dict):
    create = await client.post(
        "/api/v1/intake",
        json={
            "patient_name": "x",
            "contact_reason": "y",
            "contact_channel": "phone",
        },
        headers=admin_headers,
    )
    case_id = create.json()["id"]

    response = await client.patch(
        f"/api/v1/intake/{case_id}/status",
        json={"status": "consent_pending"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "consent_pending"
