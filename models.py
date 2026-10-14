import datetime
import pytz
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float
from database import Base

def get_current_kolkata_time():
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.datetime.now(tz)

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), unique=True, index=True, nullable=False)
    source = Column(String(100), default="Manual Entry", index=True)
    author = Column(String(200), nullable=True)
    date_discovered = Column(DateTime, default=get_current_kolkata_time, index=True)
    
    # Problem & Categorization
    stated_problem = Column(Text, nullable=False)
    industry = Column(String(100), default="SMB / General", index=True)
    country = Column(String(100), default="Unknown", index=True)
    country_confirmed = Column(Boolean, default=False)
    matching_service = Column(String(150), nullable=False, index=True)
    
    # Qualification & Scoring
    qualification_status = Column(String(50), default="Awaiting Review", index=True) # Qualified, Awaiting Review, Disqualified, Contacted, Converted
    score = Column(Integer, default=50, index=True)
    score_breakdown = Column(Text, nullable=True) # JSON string explaining clarity, relevance, evidence, feasibility
    
    # Research Notes & Personalized Response
    notes = Column(Text, nullable=True)
    suggested_response = Column(Text, nullable=True)
    response_approved = Column(Boolean, default=False)
    review_status = Column(String(50), default="Pending") # Pending, Approved, Rejected
    
    # Google Sheets Synchronization Tracking
    synced_to_sheets = Column(Boolean, default=False, index=True)
    synced_to_sheets_at = Column(DateTime, nullable=True)
    sheets_row_id = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=get_current_kolkata_time)
    updated_at = Column(DateTime, default=get_current_kolkata_time, onupdate=get_current_kolkata_time)

class DailyResearchStat(Base):
    __tablename__ = "daily_research_stats"

    id = Column(Integer, primary_key=True, index=True)
    date_str = Column(String(20), unique=True, index=True, nullable=False) # e.g. 2026-10-14 in Asia/Kolkata
    reviewed_count = Column(Integer, default=0)
    reviewed_target = Column(Integer, default=20)
    qualified_count = Column(Integer, default=0)
    qualified_target = Column(Integer, default=5)
    updated_at = Column(DateTime, default=get_current_kolkata_time)

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=get_current_kolkata_time, index=True)
    action_type = Column(String(100), nullable=False) # e.g. LEAD_CREATED, LEAD_QUALIFIED, CSV_IMPORT, SHEETS_SYNC
    description = Column(Text, nullable=False)
    lead_id = Column(Integer, nullable=True)
