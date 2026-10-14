import os
from pydantic import BaseModel, Field
from typing import Optional

class Settings(BaseModel):
    app_name: str = "Auyvra Lead Research Dashboard"
    app_env: str = os.getenv("APP_ENV", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "t")
    port: int = int(os.getenv("PORT", "8000"))
    secret_key: str = os.getenv("SECRET_KEY", "auyvra-lead-research-dev-secret-key-2026")
    timezone: str = os.getenv("TIMEZONE", "Asia/Kolkata")
    
    # Isolated Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./auyvra_leads.db")
    
    # Reddit Integration Settings (Pending Commercial Authorization)
    reddit_integration_enabled: bool = os.getenv("REDDIT_INTEGRATION_ENABLED", "false").lower() in ("true", "1", "t")
    reddit_client_id: Optional[str] = os.getenv("REDDIT_CLIENT_ID")
    reddit_client_secret: Optional[str] = os.getenv("REDDIT_CLIENT_SECRET")
    reddit_user_agent: str = os.getenv("REDDIT_USER_AGENT", "web:auyvra-lead-research:v1.0.0 (by /u/auyvra)")
    
    # Google Sheets Settings
    google_sheet_name: str = os.getenv("GOOGLE_SHEET_NAME", "Auyvra Daily Leads")
    google_service_account_file: Optional[str] = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    google_service_account_json: Optional[str] = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    
    # Alert & Reporting Settings
    alert_email_recipient: str = os.getenv("ALERT_EMAIL_RECIPIENT", "lingamanil55@gmail.com")
    dashboard_public_url: str = os.getenv("DASHBOARD_PUBLIC_URL", "http://localhost:8000")
    
    # Research Targets
    daily_review_target: int = 20
    daily_qualified_target: int = 5

settings = Settings()
