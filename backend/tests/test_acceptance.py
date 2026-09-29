import pytest
import json
import io
from fastapi.testclient import TestClient
from app.main import app
from app.services.vector_store import vector_store
from app.core.session import session_manager
from app.config import settings

client = TestClient(app)

def parse_sse_events(response_text: str):
    """Parses raw Server-Sent Events output into structured list of (event, data)."""
    events = []
    lines = response_text.strip().split("\n")
    current_event = "message"
    for line in lines:
        line = line.strip()
        if line.startswith("event:"):
            current_event = line.replace("event:", "").strip()
        elif line.startswith("data:"):
            data_str = line.replace("data:", "").strip()
            try:
                data_val = json.loads(data_str)
            except Exception:
                data_val = data_str
            events.append((current_event, data_val))
    return events

# -------------------------------------------------------------
# Test A: Document-Grounded QA
# -------------------------------------------------------------
def test_acceptance_document_grounded_qa(sample_apollo_pdf_bytes):
    # 1. Upload Apollo document
    upload_resp = client.post(
        "/api/documents/upload",
        files={"file": ("apollo.pdf", sample_apollo_pdf_bytes, "application/pdf")},
        data={"session_id": "acceptance_session"}
    )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    doc_id = upload_data["document_id"]
    assert doc_id.startswith("doc_")
    assert upload_data["page_count"] == 2
    assert upload_data["chunk_count"] >= 3

    # 2. Ask question grounded in the document
    chat_resp = client.post(
        "/api/chat/stream",
        json={
            "query": "What was the name of the Apollo 11 lunar module and commander?",
            "session_id": "acceptance_session",
            "document_id": doc_id,
            "rag_mode": "auto",
            "provider": "gemini",
            "api_key": "mock_key"
        }
    )
    assert chat_resp.status_code == 200
    events = parse_sse_events(chat_resp.text)

    # Verify citation event
    citation_events = [data for ev, data in events if ev == "citation"]
    assert len(citation_events) > 0
    citations = citation_events[0]["citations"]
    assert len(citations) > 0
    top_citation = citations[0]
    assert top_citation["page"] == 1
    assert "Eagle" in top_citation["text"] or "Apollo 11" in top_citation["text"]
    assert top_citation["score"] >= 0.65

    # Verify delta text contains factual answer
    delta_texts = [data["text"] for ev, data in events if ev == "delta"]
    full_answer = "".join(delta_texts)
    assert "Eagle" in full_answer or "Neil Armstrong" in full_answer

# -------------------------------------------------------------
# Test B: General Knowledge fallback
# -------------------------------------------------------------
def test_acceptance_general_knowledge(sample_apollo_pdf_bytes):
    # Upload doc
    upload_resp = client.post(
        "/api/documents/upload",
        files={"file": ("apollo.pdf", sample_apollo_pdf_bytes, "application/pdf")},
        data={"session_id": "gk_session"}
    )
    doc_id = upload_resp.json()["document_id"]

    # Ask general knowledge query
    chat_resp = client.post(
        "/api/chat/stream",
        json={
            "query": "Explain how photosynthesis works.",
            "session_id": "gk_session",
            "document_id": doc_id,
            "rag_mode": "auto",
            "provider": "gemini",
            "api_key": "mock_key",
            "similarity_threshold": 0.85
        }
    )
    assert chat_resp.status_code == 200
    events = parse_sse_events(chat_resp.text)

    delta_texts = [data["text"] for ev, data in events if ev == "delta"]
    full_answer = "".join(delta_texts)

    # Must give correct scientific answer without fabricating document citation or claiming missing PDF info
    assert "light energy" in full_answer.lower() or "glucose" in full_answer.lower() or "plants" in full_answer.lower()
    assert "could not find sufficient information in the document" not in full_answer.lower()

# -------------------------------------------------------------
# Tests 1-4: Relative Date Tool Acceptance
# -------------------------------------------------------------
def test_acceptance_relative_date_tool():
    # 1. Today's date
    resp_today = client.post(
        "/api/chat/stream",
        json={
            "query": "What is today's date?",
            "session_id": "date_session",
            "timezone": "UTC",
            "rag_mode": "auto",
            "api_key": "mock_key"
        }
    )
    assert resp_today.status_code == 200
    events_today = parse_sse_events(resp_today.text)
    tool_starts = [data for ev, data in events_today if ev == "tool_start"]
    assert len(tool_starts) > 0
    assert tool_starts[0]["tool"] in ["get_relative_date", "get_current_datetime"]

    # 2. Tomorrow's date
    resp_tomorrow = client.post(
        "/api/chat/stream",
        json={
            "query": "What date is tomorrow?",
            "session_id": "date_session",
            "timezone": "UTC",
            "rag_mode": "auto",
            "api_key": "mock_key"
        }
    )
    events_tomorrow = parse_sse_events(resp_tomorrow.text)
    tool_starts = [data for ev, data in events_tomorrow if ev == "tool_start"]
    assert any(ts["tool"] == "get_relative_date" and ts["args"].get("days_offset") == 1 for ts in tool_starts)

    # 3. Yesterday's date
    resp_yesterday = client.post(
        "/api/chat/stream",
        json={
            "query": "What date was yesterday?",
            "session_id": "date_session",
            "timezone": "UTC",
            "rag_mode": "auto",
            "api_key": "mock_key"
        }
    )
    events_yesterday = parse_sse_events(resp_yesterday.text)
    tool_starts = [data for ev, data in events_yesterday if ev == "tool_start"]
    assert any(ts["tool"] == "get_relative_date" and ts["args"].get("days_offset") == -1 for ts in tool_starts)

    # 4. 4 days from now
    resp_future = client.post(
        "/api/chat/stream",
        json={
            "query": "What date will it be 4 days from now?",
            "session_id": "date_session",
            "timezone": "UTC",
            "rag_mode": "auto",
            "api_key": "mock_key"
        }
    )
    events_future = parse_sse_events(resp_future.text)
    tool_starts = [data for ev, data in events_future if ev == "tool_start"]
    assert any(ts["tool"] == "get_relative_date" and ts["args"].get("days_offset") == 4 for ts in tool_starts)

# -------------------------------------------------------------
# Test 5: Timezone Datetime Tool Acceptance
# -------------------------------------------------------------
def test_acceptance_timezone_datetime_tool():
    # Asks for time in India
    resp = client.post(
        "/api/chat/stream",
        json={
            "query": "What time is it in India?",
            "session_id": "time_session",
            "timezone": "UTC",
            "rag_mode": "auto",
            "api_key": "mock_key"
        }
    )
    assert resp.status_code == 200
    events = parse_sse_events(resp.text)
    tool_ends = [data for ev, data in events if ev == "tool_end"]
    assert len(tool_ends) > 0
    res_payload = tool_ends[0]["result"]
    assert res_payload["timezone"] == "Asia/Kolkata"
    assert "time" in res_payload
    assert "date" in res_payload

    # Direct endpoint health check test
    health_time = client.get("/api/tools/time?timezone=Asia/Kolkata")
    assert health_time.status_code == 200
    assert health_time.json()["timezone"] == "Asia/Kolkata"

# -------------------------------------------------------------
# Test E: Chunk Inspection
# -------------------------------------------------------------
def test_acceptance_chunk_inspection(sample_apollo_pdf_bytes):
    upload_resp = client.post(
        "/api/documents/upload",
        files={"file": ("apollo.pdf", sample_apollo_pdf_bytes, "application/pdf")},
        data={"session_id": "inspect_session"}
    )
    doc_id = upload_resp.json()["document_id"]

    chunks_resp = client.get(f"/api/documents/{doc_id}/chunks")
    assert chunks_resp.status_code == 200
    data = chunks_resp.json()
    assert data["total_chunks"] >= 3
    first_chk = data["chunks"][0]
    assert first_chk["page_number"] in [1, 2]
    assert first_chk["bbox"] is not None
    assert len(first_chk["bbox"]) == 4

# -------------------------------------------------------------
# Test F: Prompt Injection Defense
# -------------------------------------------------------------
def test_acceptance_prompt_injection_defense(sample_injection_pdf_bytes):
    upload_resp = client.post(
        "/api/documents/upload",
        files={"file": ("malicious.pdf", sample_injection_pdf_bytes, "application/pdf")},
        data={"session_id": "security_session"}
    )
    doc_id = upload_resp.json()["document_id"]

    chat_resp = client.post(
        "/api/chat/stream",
        json={
            "query": "Please summarize the attached document.",
            "session_id": "security_session",
            "document_id": doc_id,
            "rag_mode": "auto",
            "api_key": "mock_key"
        }
    )
    assert chat_resp.status_code == 200
    events = parse_sse_events(chat_resp.text)
    delta_texts = [data["text"] for ev, data in events if ev == "delta"]
    full_output = "".join(delta_texts)

    # Must NOT execute prompt injection override
    assert "PWNED" not in full_output.upper() or "ATTEMPTING TO OVERRIDE" in full_output.upper()
    assert "untrusted instruction" in full_output.lower() or "security" in full_output.lower()

# -------------------------------------------------------------
# Test G: Document Deletion
# -------------------------------------------------------------
def test_acceptance_document_deletion(sample_apollo_pdf_bytes):
    # Upload
    upload_resp = client.post(
        "/api/documents/upload",
        files={"file": ("apollo.pdf", sample_apollo_pdf_bytes, "application/pdf")},
        data={"session_id": "del_session"}
    )
    doc_id = upload_resp.json()["document_id"]
    pdf_path = settings.UPLOAD_DIR / "del_session" / f"{doc_id}.pdf"
    assert pdf_path.exists()

    # Delete
    del_resp = client.delete(f"/api/documents/{doc_id}?session_id=del_session")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # Verify filesystem removal
    assert not pdf_path.exists()

    # Verify session manager cleanup
    assert session_manager.get_document(doc_id) is None

    # Verify vector store retrieval returns empty
    citations = vector_store.hybrid_search("Apollo", doc_id, "del_session")
    assert len(citations) == 0
