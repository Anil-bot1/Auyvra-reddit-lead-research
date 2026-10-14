import json
import os
import datetime
import pytz
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from models import Lead
from config import settings
from services.lead_service import log_activity

HEADERS = [
    "Lead ID",
    "Discovered Date",
    "Source",
    "Discussion Title",
    "Discussion URL",
    "Country",
    "Country Confirmed",
    "Industry",
    "Stated Problem",
    "Matching Auyvra Service",
    "Lead Score",
    "Qualification Status",
    "Score Reasons",
    "Admin Notes",
    "Suggested Reply Draft",
    "Review Status",
    "Synced At"
]

class GoogleSheetsService:
    @staticmethod
    def is_configured() -> bool:
        return bool(settings.google_service_account_file or settings.google_service_account_json)

    @classmethod
    def get_client(cls):
        """
        Initializes gspread client using Service Account credentials.
        Never throws unhandled exceptions; returns client or raises ValueError.
        """
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        if settings.google_service_account_json:
            try:
                info = json.loads(settings.google_service_account_json)
                credentials = Credentials.from_service_account_info(info, scopes=scopes)
                return gspread.authorize(credentials)
            except Exception as e:
                raise ValueError(f"Failed to parse GOOGLE_SERVICE_ACCOUNT_JSON: {str(e)}")

        if settings.google_service_account_file:
            if not os.path.exists(settings.google_service_account_file):
                raise FileNotFoundError(f"Service account file not found: {settings.google_service_account_file}")
            credentials = Credentials.from_service_account_file(settings.google_service_account_file, scopes=scopes)
            return gspread.authorize(credentials)

        raise ValueError("Google Sheets credentials are not configured.")

    @classmethod
    def sync_leads_to_sheet(cls, db: Session, target_date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Safely appends unsynced leads to a daily worksheet named Leads_YYYY-MM-DD
        in the spreadsheet 'Auyvra Daily Leads'.
        """
        if not cls.is_configured():
            return {
                "success": False,
                "configured": False,
                "synced_count": 0,
                "message": (
                    "Google Sheets credentials not configured. The app is storing leads locally in auyvra_leads.db. "
                    "To enable sync, add your Google Service Account JSON to .env."
                )
            }

        try:
            client = cls.get_client()
        except Exception as e:
            return {
                "success": False,
                "configured": True,
                "synced_count": 0,
                "message": f"Authentication error: {str(e)}"
            }

        tz = pytz.timezone(settings.timezone)
        if not target_date_str:
            target_date_str = datetime.datetime.now(tz).strftime("%Y-%m-%d")

        tab_name = f"Leads_{target_date_str}"

        try:
            spreadsheet = client.open(settings.google_sheet_name)
        except Exception as e:
            return {
                "success": False,
                "configured": True,
                "synced_count": 0,
                "message": f"Could not open spreadsheet '{settings.google_sheet_name}'. Verify the sheet exists and is shared with your Service Account email with 'Editor' permissions. Error: {str(e)}"
            }

        # Select or create the daily worksheet
        try:
            worksheet = spreadsheet.worksheet(tab_name)
        except Exception:
            try:
                worksheet = spreadsheet.add_worksheet(title=tab_name, rows=500, cols=len(HEADERS))
                worksheet.append_row(HEADERS)
            except Exception as e:
                return {
                    "success": False,
                    "configured": True,
                    "synced_count": 0,
                    "message": f"Failed to create daily worksheet '{tab_name}': {str(e)}"
                }

        # Check existing URLs to prevent duplicate rows in the sheet
        try:
            existing_records = worksheet.get_all_values()
            existing_urls = set()
            if len(existing_records) > 1:
                # Column 5 (0-indexed is 4) is 'Discussion URL'
                for row in existing_records[1:]:
                    if len(row) > 4 and row[4]:
                        existing_urls.add(row[4].strip())
        except Exception:
            existing_urls = set()

        # Query unsynced leads
        leads_to_sync = db.query(Lead).filter(
            Lead.synced_to_sheets == False,
            Lead.qualification_status.in_(["Qualified", "Awaiting Review"])
        ).all()

        if not leads_to_sync:
            return {
                "success": True,
                "configured": True,
                "synced_count": 0,
                "message": f"All qualified and review leads are already synced to worksheet '{tab_name}'."
            }

        rows_to_append = []
        synced_lead_objects = []
        current_time_str = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

        for lead in leads_to_sync:
            if lead.url.strip() in existing_urls:
                lead.synced_to_sheets = True
                lead.synced_to_sheets_at = datetime.datetime.now(tz)
                continue

            # Extract reasons text from score_breakdown JSON
            reasons_text = ""
            if lead.score_breakdown:
                try:
                    sb = json.loads(lead.score_breakdown)
                    if isinstance(sb, dict) and "reasons" in sb:
                        reasons_text = " | ".join(sb["reasons"])
                except Exception:
                    reasons_text = str(lead.score_breakdown)

            row = [
                lead.id,
                lead.date_discovered.strftime("%Y-%m-%d %H:%M") if lead.date_discovered else "",
                lead.source or "Manual Entry",
                lead.title,
                lead.url,
                lead.country,
                "Yes" if lead.country_confirmed else "No (Inferred/Unknown)",
                lead.industry,
                lead.stated_problem,
                lead.matching_service,
                lead.score,
                lead.qualification_status,
                reasons_text,
                lead.notes or "",
                lead.suggested_response or "",
                lead.review_status,
                current_time_str
            ]
            rows_to_append.append(row)
            synced_lead_objects.append(lead)

        if rows_to_append:
            try:
                worksheet.append_rows(rows_to_append)
                for lead in synced_lead_objects:
                    lead.synced_to_sheets = True
                    lead.synced_to_sheets_at = datetime.datetime.now(tz)
                db.commit()
                log_activity(db, "SHEETS_SYNC", f"Synced {len(rows_to_append)} leads to Google Sheet tab '{tab_name}'")
            except Exception as e:
                return {
                    "success": False,
                    "configured": True,
                    "synced_count": 0,
                    "message": f"Error appending rows to Google Sheet: {str(e)}"
                }

        return {
            "success": True,
            "configured": True,
            "synced_count": len(rows_to_append),
            "worksheet": tab_name,
            "message": f"Successfully synced {len(rows_to_append)} leads to Google Sheet tab '{tab_name}'."
        }
