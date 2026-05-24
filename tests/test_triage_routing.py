from httpx import AsyncClient


async def _create_case(client: AsyncClient, headers: dict, reason: str = "general") -> str:
    response = await client.post(
        "/api/v1/intake",
        json={
            "patient_name": "Triage Tester",
            "contact_reason": reason,
            "contact_channel": "phone",
        },
        headers=headers,
    )
    return response.json()["id"]


async def test_triage_routine(client: AsyncClient, admin_headers: dict):
    case_id = await _create_case(client, admin_headers)
    response = await client.post(
        "/api/v1/triage",
        json={
            "case_id": case_id,
            "contact_reason": "I would like to update my address on file please",
            "keywords": [],
            "patient_priority_flags": [],
        },
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "routine"
    assert body["escalated"] is False
    assert body["routing_action"] == "admin_workflow"


async def test_triage_urgent_keyword(client: AsyncClient, admin_headers: dict):
    case_id = await _create_case(client, admin_headers)
    response = await client.post(
        "/api/v1/triage",
        json={
            "case_id": case_id,
            "contact_reason": "this is urgent please call back",
            "keywords": [],
            "patient_priority_flags": [],
        },
        headers=admin_headers,
    )
    assert response.json()["category"] == "immediate"
    assert response.json()["escalated"] is True


async def test_triage_multi_word_phrase_chest_pain(client: AsyncClient, admin_headers: dict):
    """Regression: original code did set intersection on whitespace tokens,
    so 'chest pain' never matched. Substring match fixes it."""
    case_id = await _create_case(client, admin_headers)
    response = await client.post(
        "/api/v1/triage",
        json={
            "case_id": case_id,
            "contact_reason": "patient reports chest pain and dizziness",
            "keywords": [],
            "patient_priority_flags": [],
        },
        headers=admin_headers,
    )
    assert response.json()["category"] == "immediate"


async def test_triage_patient_flag_escalates(client: AsyncClient, admin_headers: dict):
    """Regression: original code treated patient priority flags as a
    low-confidence signal. They should escalate, not de-escalate."""
    case_id = await _create_case(client, admin_headers)
    response = await client.post(
        "/api/v1/triage",
        json={
            "case_id": case_id,
            "contact_reason": "need to reschedule appointment next week",
            "keywords": [],
            "patient_priority_flags": ["high_priority_patient"],
        },
        headers=admin_headers,
    )
    assert response.json()["category"] == "time_sensitive"
    assert response.json()["escalated"] is True


async def test_triage_then_routing(client: AsyncClient, admin_headers: dict):
    case_id = await _create_case(client, admin_headers)
    triage = await client.post(
        "/api/v1/triage",
        json={
            "case_id": case_id,
            "contact_reason": "regular check up booking please thanks",
            "keywords": [],
            "patient_priority_flags": [],
        },
        headers=admin_headers,
    )
    triage_id = triage.json()["triage_id"]

    routing = await client.post(
        "/api/v1/routing",
        json={"triage_id": triage_id},
        headers=admin_headers,
    )
    assert routing.status_code == 201
    assert routing.json()["action"] == "admin_workflow"
    assert routing.json()["case_id"] == case_id
    assert routing.json()["triage_id"] == triage_id
