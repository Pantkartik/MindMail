import json
import asyncio

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.rag.pipeline import EmailRAGPipeline
from backend.tools.calendar import CalendarToolManager
from backend.tools.gmail import GmailToolManager


client = TestClient(app)


def test_health_reports_local_demo_mode():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["mode"] == "local_demo"
    assert response.json()["integrations"] == "mock"


def test_frontend_is_served_from_the_api_root():
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "MailMind" in response.text


def test_frontend_styles_and_script_are_served():
    css_response = client.get("/styles.css")
    js_response = client.get("/app.js")

    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert js_response.status_code == 200
    assert "javascript" in js_response.headers["content-type"]


def test_dashboard_overview_marks_fixtures_as_sample_data():
    response = client.get("/api/v1/demo/overview")

    assert response.status_code == 200
    overview = response.json()
    assert overview["sample_data"] is True
    assert overview["emails"]
    assert overview["events"]


def test_chat_stream_labels_fixture_data():
    response = client.post(
        "/api/v1/chat",
        json={"message": "What is on my schedule?"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: {")
    ]
    content = next(event for event in events if event["type"] == "content")
    assert "Local demo only" in content["text"]
    assert content["query"] == "What is on my schedule?"
    assert content["citations"]
    assert all("(sample)" in citation["source"] for citation in content["citations"])


def test_chat_rejects_empty_and_oversized_messages():
    assert client.post("/api/v1/chat", json={"message": ""}).status_code == 422
    assert client.post("/api/v1/chat", json={"message": "x" * 4001}).status_code == 422


def test_approval_fails_closed_instead_of_claiming_to_send():
    response = client.post(
        "/api/v1/chat/approve",
        json={"thread_id": "local-demo", "approved": True},
    )

    assert response.status_code == 501
    assert "no action was executed" in response.json()["detail"]


def test_memory_endpoint_does_not_invent_preferences():
    response = client.get("/api/v1/memory")

    assert response.status_code == 200
    assert response.json() == {"configured": False, "preferences": {}}


def test_cors_does_not_allow_arbitrary_origins_or_credentials():
    response = client.options(
        "/api/v1/chat",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert "access-control-allow-origin" not in response.headers
    assert "access-control-allow-credentials" not in response.headers


def test_unconfigured_gmail_does_not_claim_to_send():
    try:
        GmailToolManager().send_email("someone@example.com", "Hello", "Body")
    except RuntimeError as error:
        assert "no email was sent" in str(error)
    else:
        raise AssertionError("Unconfigured Gmail must not report a successful send.")


def test_calendar_availability_does_not_claim_a_slot_is_free():
    try:
        CalendarToolManager().check_availability("2026-11-28T10:00:00Z", "2026-11-28T11:00:00Z")
    except NotImplementedError:
        pass
    else:
        raise AssertionError("Unimplemented availability checks must fail explicitly.")


def test_rag_does_not_return_fabricated_results():
    pipeline = EmailRAGPipeline()
    try:
        asyncio.run(pipeline.hybrid_search("user", "interview"))
    except NotImplementedError:
        pass
    else:
        raise AssertionError("Unimplemented RAG search must fail explicitly.")
