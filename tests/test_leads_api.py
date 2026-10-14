import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.pool import StaticPool
from database import Base, get_db
from main import app
from models import Lead, DailyResearchStat, ActivityLog

# Use an in-memory test database with StaticPool so all threads/sessions share the same database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["reddit_integration"] == "disabled_pending_approval"

def test_create_and_deduplicate_lead():
    payload = {
        "title": "Struggling with missed calls at our dental clinic",
        "url": "https://example.com/discussions/dental-calls-1",
        "stated_problem": "Our dental practice in Toronto is missing phone calls and we need automated booking.",
        "source": "Manual Entry"
    }
    
    # 1. Create lead
    response = client.post("/api/leads", json=payload)
    assert response.status_code == 200
    lead = response.json()
    assert lead["id"] is not None
    assert lead["url"] == payload["url"]
    assert lead["score"] >= 60

    # 2. Attempt duplicate creation with same URL -> 409 Conflict
    response_dup = client.post("/api/leads", json=payload)
    assert response_dup.status_code == 409
    assert "already exists" in response_dup.json()["detail"]

def test_parse_notes():
    text = (
        "Restaurant in Sydney Australia losing table reservations because staff cannot answer phone calls during dinner rush. "
        "Looking for recommendations on automated receptionist or phone bots."
    )
    res = client.post("/api/leads/parse-notes", json={"raw_text": text})
    assert res.status_code == 200
    data = res.json()
    assert data["country"] == "Australia"
    assert data["industry"] == "Restaurant / Catering"
    assert "Receptionist" in data["matching_service"] or "Voice Agent" in data["matching_service"]
    assert data["score"] >= 65

def test_csv_import_validation_and_dedup():
    csv_data = """url,title,stated_problem,industry,country
https://example.com/disc/2,Real estate leads ghosting,We need follow up automation for cold buyer inquiries,Real Estate,United States
https://example.com/disc/3,Home services dispatch delays,Plumbing company having trouble routing emergency service calls,Home Services,United Kingdom
invalid-url-line,No URL,This row has an invalid URL,Agency,India
"""
    files = {"file": ("test_leads.csv", csv_data, "text/csv")}
    res = client.post("/api/leads/import-csv", files=files)
    assert res.status_code == 200
    result = res.json()
    assert result["imported_count"] == 2
    assert result["error_count"] == 1
    assert "Invalid or missing URL" in result["errors"][0]

def test_sheets_graceful_fallback():
    # Calling sync when Google Sheets credentials are not provided should return graceful error, NOT crash with 500
    res = client.post("/api/sync/sheets")
    assert res.status_code == 200
    data = res.json()
    assert data["configured"] is False
    assert "Google Sheets credentials not configured" in data["message"]

def test_daily_report_preview():
    res = client.get("/api/report/preview")
    assert res.status_code == 200
    data = res.json()
    assert "html_content" in data
    assert "Auyvra" in data["subject"]

def test_dashboard_html_page():
    res = client.get("/")
    assert res.status_code == 200
    assert "Auyvra" in res.text
    assert "Lead Research" in res.text

def test_update_and_delete_lead():
    # Create a lead to update
    payload = {
        "title": "Lead to update",
        "url": "https://example.com/update-test-1",
        "stated_problem": "Staff missing phone calls in dental practice",
        "industry": "Dental Practice",
        "country": "India"
    }
    create_res = client.post("/api/leads", json=payload)
    lead_id = create_res.json()["id"]

    # Patch lead
    patch_res = client.patch(f"/api/leads/{lead_id}", json={
        "qualification_status": "Contacted",
        "score": 95,
        "notes": "Followed up with owner"
    })
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["qualification_status"] == "Contacted"
    assert updated["score"] == 95
    assert updated["notes"] == "Followed up with owner"

    # Delete lead
    del_res = client.delete(f"/api/leads/{lead_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

def test_export_leads():
    # Test CSV export
    res_csv = client.get("/api/leads/export?format=csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]

    # Test JSON export
    res_json = client.get("/api/leads/export?format=json")
    assert res_json.status_code == 200
    assert isinstance(res_json.json(), list)

def test_apps_script_code_endpoint():
    res = client.get("/api/report/apps-script")
    assert res.status_code == 200
    data = res.json()
    assert "sendDailyLeadDigest" in data["code"]

