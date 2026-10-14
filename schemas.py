from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime

class LeadCreate(BaseModel):
    title: str = Field(..., description="Discussion title or subject")
    url: str = Field(..., description="Full URL to the discussion")
    source: str = Field(default="Manual Entry", description="Subreddit, forum, or source channel")
    author: Optional[str] = Field(default=None, description="Username or author handle if public")
    stated_problem: str = Field(..., description="Stated operational problem or bottleneck")
    industry: Optional[str] = Field(default="SMB / General", description="Detected or specified industry")
    country: Optional[str] = Field(default="Unknown", description="Country if known")
    country_confirmed: bool = Field(default=False, description="Whether country is verified")
    matching_service: Optional[str] = Field(default=None, description="Matching Auyvra service")
    notes: Optional[str] = Field(default=None, description="Research or context notes")
    score: Optional[int] = Field(default=None, ge=0, le=100, description="Manual or calculated score")
    qualification_status: Optional[str] = Field(default=None, description="Qualified, Awaiting Review, Disqualified, etc.")

class LeadUpdate(BaseModel):
    title: Optional[str] = None
    stated_problem: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    country_confirmed: Optional[bool] = None
    matching_service: Optional[str] = None
    qualification_status: Optional[str] = None
    score: Optional[int] = Field(default=None, ge=0, le=100)
    notes: Optional[str] = None
    suggested_response: Optional[str] = None
    response_approved: Optional[bool] = None
    review_status: Optional[str] = None

class LeadOut(BaseModel):
    id: int
    title: str
    url: str
    source: str
    author: Optional[str]
    date_discovered: datetime
    stated_problem: str
    industry: str
    country: str
    country_confirmed: bool
    matching_service: str
    qualification_status: str
    score: int
    score_breakdown: Optional[str]
    notes: Optional[str]
    suggested_response: Optional[str]
    response_approved: bool
    review_status: str
    synced_to_sheets: bool
    synced_to_sheets_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class LeadParseRequest(BaseModel):
    raw_text: str = Field(..., description="Raw text snippet or copied discussion post")
    url: Optional[str] = None
    source: Optional[str] = "Manual Entry"

class LeadParseResponse(BaseModel):
    title: str
    stated_problem: str
    industry: str
    country: str
    matching_service: str
    score: int
    score_breakdown: Dict[str, Any]
    suggested_response: str
    recommended_status: str

class CsvImportResult(BaseModel):
    total_rows: int
    imported_count: int
    duplicate_count: int
    error_count: int
    errors: List[str]

class TargetStat(BaseModel):
    date_str: str
    reviewed_count: int
    reviewed_target: int
    qualified_count: int
    qualified_target: int
    reviewed_progress_pct: float
    qualified_progress_pct: float

class DashboardStats(BaseModel):
    total_leads: int
    qualified_leads: int
    awaiting_review: int
    disqualified_leads: int
    contacted_leads: int
    average_score: float
    daily_target: TargetStat
    country_breakdown: Dict[str, int]
    industry_breakdown: Dict[str, int]
    service_breakdown: Dict[str, int]
    score_distribution: Dict[str, int] # High (75-100), Medium (50-74), Low (<50)
    recent_activity: List[Dict[str, Any]]
    reddit_mode: str # "Disabled (Awaiting Commercial Approval)" or "Active"
    sheets_status: str
