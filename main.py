import io
import csv
import json
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import settings
from database import engine, Base, get_db
from models import Lead
from schemas import (
    LeadCreate,
    LeadUpdate,
    LeadOut,
    LeadParseRequest,
    LeadParseResponse,
    CsvImportResult,
    DashboardStats
)
from services.lead_service import LeadService, log_activity
from services.sheets_service import GoogleSheetsService
from services.report_service import ReportService
from sources.manual import ManualLeadSource

# Initialize tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="Professional Lead Research & Qualification Dashboard for Auyvra AI Automation Agency",
    version="1.0.0"
)

import os

# Ensure static and template directories exist
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Static and template setup
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

manual_source = ManualLeadSource()

# ==========================================
# Frontend Routes
# ==========================================
@app.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: Session = Depends(get_db)):
    stats = LeadService.get_dashboard_stats(db)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "app_name": settings.app_name,
            "stats": stats,
            "settings": settings
        }
    )

# ==========================================
# API Endpoints
# ==========================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env,
        "reddit_integration": "disabled_pending_approval" if not settings.reddit_integration_enabled else "active",
        "sheets_sync_configured": GoogleSheetsService.is_configured()
    }

@app.get("/api/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    return LeadService.get_dashboard_stats(db)

@app.get("/api/leads", response_model=List[LeadOut])
def list_leads(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None),
    max_score: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    leads, _ = LeadService.get_leads(
        db=db,
        search=search,
        status=status,
        country=country,
        industry=industry,
        service=service,
        min_score=min_score,
        max_score=max_score,
        skip=skip,
        limit=limit
    )
    return leads

@app.get("/api/leads/export")
def export_leads(
    export_format: str = Query("csv", alias="format"),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if export_format not in ("csv", "json"):
        raise HTTPException(status_code=400, detail="Invalid format. Use 'csv' or 'json'.")

    leads, _ = LeadService.get_leads(db, status=status, limit=10000)
    
    if export_format == "json":
        data = [LeadOut.model_validate(lead).model_dump(mode="json") for lead in leads]
        return JSONResponse(content=data)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Lead ID", "Date Discovered", "Source", "Title", "URL",
        "Country", "Country Confirmed", "Industry", "Stated Problem",
        "Matching Service", "Score", "Status", "Notes", "Review Status"
    ])
    for l in leads:
        writer.writerow([
            l.id,
            l.date_discovered.strftime("%Y-%m-%d %H:%M") if l.date_discovered else "",
            l.source,
            l.title,
            l.url,
            l.country,
            l.country_confirmed,
            l.industry,
            l.stated_problem,
            l.matching_service,
            l.score,
            l.qualification_status,
            l.notes or "",
            l.review_status
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=auyvra_leads_export.csv"}
    )

@app.post("/api/leads", response_model=LeadOut)
def create_lead(lead_in: LeadCreate, db: Session = Depends(get_db)):
    lead, created, message = LeadService.create_lead(db, lead_in)
    if not created:
        raise HTTPException(status_code=409, detail=message)
    return lead

@app.get("/api/leads/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = LeadService.get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@app.patch("/api/leads/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: int, lead_update: LeadUpdate, db: Session = Depends(get_db)):
    lead = LeadService.update_lead(db, lead_id, lead_update)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@app.delete("/api/leads/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    success = LeadService.delete_lead(db, lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"success": True, "message": f"Lead #{lead_id} deleted."}

@app.post("/api/leads/parse-notes", response_model=LeadParseResponse)
def parse_notes(payload: LeadParseRequest):
    """
    Parses unstructured discussion text or notes to auto-extract problem,
    industry, country, matching Auyvra service, lead score, and reply draft.
    """
    if not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="Raw text cannot be empty.")
    
    parsed = manual_source.parse_discussion(payload.raw_text, payload.url)
    return LeadParseResponse(
        title=parsed["title"],
        stated_problem=parsed["stated_problem"],
        industry=parsed["industry"],
        country=parsed["country"],
        matching_service=parsed["matching_service"],
        score=parsed["score"],
        score_breakdown=parsed["score_breakdown"],
        suggested_response=parsed["suggested_response"],
        recommended_status=parsed["recommended_status"]
    )

@app.post("/api/leads/import-csv", response_model=CsvImportResult)
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    content = await file.read()
    try:
        csv_text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            csv_text = content.decode("latin-1")
        except Exception:
            raise HTTPException(status_code=400, detail="Unable to decode CSV file. Please use UTF-8.")

    valid_records, errors = manual_source.process_csv(csv_text)

    imported_count = 0
    duplicate_count = 0

    for rec in valid_records:
        lead_in = LeadCreate(
            title=rec["title"],
            url=rec["url"],
            stated_problem=rec["stated_problem"],
            industry=rec["industry"],
            country=rec["country"],
            country_confirmed=rec["country_confirmed"],
            source=rec["source"],
            author=rec["author"],
            matching_service=rec["matching_service"],
            score=rec["score"],
            qualification_status=rec["qualification_status"],
            notes=rec["notes"]
        )
        _, created, _ = LeadService.create_lead(db, lead_in)
        if created:
            imported_count += 1
        else:
            duplicate_count += 1

    log_activity(
        db,
        "CSV_IMPORT",
        f"Imported {imported_count} leads from '{file.filename}' ({duplicate_count} duplicates skipped, {len(errors)} row errors)"
    )

    return CsvImportResult(
        total_rows=len(valid_records) + len(errors),
        imported_count=imported_count,
        duplicate_count=duplicate_count,
        error_count=len(errors),
        errors=errors
    )

@app.post("/api/sync/sheets")
def sync_to_google_sheets(db: Session = Depends(get_db)):
    result = GoogleSheetsService.sync_leads_to_sheet(db)
    return result

@app.get("/api/report/preview")
def preview_report(db: Session = Depends(get_db)):
    digest = ReportService.generate_daily_digest(db)
    return digest

@app.get("/api/report/apps-script")
def get_apps_script():
    code = ReportService.get_google_apps_script_code()
    return {"code": code}
