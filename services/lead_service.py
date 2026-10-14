import json
import datetime
import pytz
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func
from models import Lead, DailyResearchStat, ActivityLog
from schemas import LeadCreate, LeadUpdate
from scoring import (
    calculate_lead_score,
    detect_matching_service,
    detect_industry,
    detect_country
)
from response_generator import generate_personalized_response
from config import settings

def get_today_kolkata_str() -> str:
    tz = pytz.timezone(settings.timezone)
    return datetime.datetime.now(tz).strftime("%Y-%m-%d")

def log_activity(db: Session, action_type: str, description: str, lead_id: Optional[int] = None):
    entry = ActivityLog(
        action_type=action_type,
        description=description,
        lead_id=lead_id
    )
    db.add(entry)
    db.commit()

def increment_daily_stat(db: Session, is_qualified: bool = False):
    today_str = get_today_kolkata_str()
    stat = db.query(DailyResearchStat).filter_by(date_str=today_str).first()
    if not stat:
        stat = DailyResearchStat(
            date_str=today_str,
            reviewed_count=1,
            reviewed_target=settings.daily_review_target,
            qualified_count=1 if is_qualified else 0,
            qualified_target=settings.daily_qualified_target
        )
        db.add(stat)
    else:
        stat.reviewed_count += 1
        if is_qualified:
            stat.qualified_count += 1
        stat.updated_at = datetime.datetime.now(pytz.timezone(settings.timezone))
    db.commit()

class LeadService:
    @staticmethod
    def get_leads(
        db: Session,
        search: Optional[str] = None,
        status: Optional[str] = None,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        service: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Lead], int]:
        query = db.query(Lead)

        if search:
            search_fmt = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Lead.title.ilike(search_fmt),
                    Lead.stated_problem.ilike(search_fmt),
                    Lead.notes.ilike(search_fmt),
                    Lead.url.ilike(search_fmt)
                )
            )

        if status and status != "All":
            query = query.filter(Lead.qualification_status == status)

        if country and country != "All":
            query = query.filter(Lead.country == country)

        if industry and industry != "All":
            query = query.filter(Lead.industry == industry)

        if service and service != "All":
            query = query.filter(Lead.matching_service == service)

        if min_score is not None:
            query = query.filter(Lead.score >= min_score)

        if max_score is not None:
            query = query.filter(Lead.score <= max_score)

        total_count = query.count()
        leads = query.order_by(desc(Lead.created_at)).offset(skip).limit(limit).all()
        return leads, total_count

    @staticmethod
    def get_lead_by_id(db: Session, lead_id: int) -> Optional[Lead]:
        return db.query(Lead).filter(Lead.id == lead_id).first()

    @staticmethod
    def get_lead_by_url(db: Session, url: str) -> Optional[Lead]:
        return db.query(Lead).filter(Lead.url == url.strip()).first()

    @staticmethod
    def create_lead(db: Session, lead_in: LeadCreate) -> Tuple[Optional[Lead], bool, str]:
        """
        Creates a lead with deduplication by URL.
        Returns: (lead_instance, is_created, message)
        """
        clean_url = lead_in.url.strip()
        existing = db.query(Lead).filter(Lead.url == clean_url).first()
        if existing:
            return existing, False, f"Lead with URL '{clean_url}' already exists (ID: {existing.id})."

        # Detect service, industry, country if not explicitly provided
        full_text = f"{lead_in.title} {lead_in.stated_problem}"
        
        industry = lead_in.industry or "SMB / General"
        if not lead_in.industry or lead_in.industry == "SMB / General":
            detected_ind, _ = detect_industry(full_text)
            industry = detected_ind

        country = lead_in.country or "Unknown"
        country_confirmed = lead_in.country_confirmed
        if not lead_in.country or lead_in.country == "Unknown":
            detected_cntry, confirmed = detect_country(full_text)
            country = detected_cntry
            country_confirmed = confirmed

        matching_service = lead_in.matching_service
        if not matching_service:
            detected_srv, _ = detect_matching_service(full_text)
            matching_service = detected_srv

        # Calculate score and reasoning breakdown
        score_data = calculate_lead_score(
            title=lead_in.title,
            problem_text=lead_in.stated_problem,
            industry=industry,
            country=country,
            matching_service=matching_service
        )

        final_score = lead_in.score if lead_in.score is not None else score_data["total_score"]
        final_status = lead_in.qualification_status or score_data["recommended_status"]

        # Generate consultative reply draft
        suggested_response = generate_personalized_response(
            title=lead_in.title,
            problem_text=lead_in.stated_problem,
            industry=industry,
            matching_service=matching_service,
            author=lead_in.author
        )

        lead = Lead(
            title=lead_in.title,
            url=clean_url,
            source=lead_in.source or "Manual Entry",
            author=lead_in.author,
            stated_problem=lead_in.stated_problem,
            industry=industry,
            country=country,
            country_confirmed=country_confirmed,
            matching_service=matching_service,
            qualification_status=final_status,
            score=final_score,
            score_breakdown=json.dumps(score_data),
            notes=lead_in.notes,
            suggested_response=suggested_response,
            response_approved=False,
            review_status="Pending"
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        # Update daily target tracker and activity log
        is_qual = final_status == "Qualified"
        increment_daily_stat(db, is_qualified=is_qual)
        log_activity(db, "LEAD_CREATED", f"Added lead #{lead.id}: '{lead.title[:50]}...' ({matching_service})", lead.id)

        return lead, True, "Lead successfully created."

    @staticmethod
    def update_lead(db: Session, lead_id: int, lead_update: LeadUpdate) -> Optional[Lead]:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return None

        update_data = lead_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lead, field, value)

        lead.updated_at = datetime.datetime.now(pytz.timezone(settings.timezone))
        db.commit()
        db.refresh(lead)

        log_activity(db, "LEAD_UPDATED", f"Updated lead #{lead.id} details (Status: {lead.qualification_status}, Score: {lead.score})", lead.id)
        return lead

    @staticmethod
    def delete_lead(db: Session, lead_id: int) -> bool:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return False
        log_activity(db, "LEAD_DELETED", f"Deleted lead #{lead.id} ('{lead.title[:50]}')", lead.id)
        db.delete(lead)
        db.commit()
        return True

    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict[str, Any]:
        total_leads = db.query(Lead).count()
        qualified_leads = db.query(Lead).filter(Lead.qualification_status == "Qualified").count()
        awaiting_review = db.query(Lead).filter(Lead.qualification_status == "Awaiting Review").count()
        disqualified_leads = db.query(Lead).filter(Lead.qualification_status == "Disqualified").count()
        contacted_leads = db.query(Lead).filter(Lead.qualification_status.in_(["Contacted", "Converted"])).count()

        avg_score_res = db.query(func.avg(Lead.score)).scalar()
        average_score = round(float(avg_score_res), 1) if avg_score_res else 0.0

        # Country distribution
        countries = db.query(Lead.country, func.count(Lead.id)).group_by(Lead.country).all()
        country_breakdown = {c[0]: c[1] for c in countries if c[0]}

        # Industry distribution
        industries = db.query(Lead.industry, func.count(Lead.id)).group_by(Lead.industry).all()
        industry_breakdown = {i[0]: i[1] for i in industries if i[0]}

        # Service distribution
        services = db.query(Lead.matching_service, func.count(Lead.id)).group_by(Lead.matching_service).all()
        service_breakdown = {s[0]: s[1] for s in services if s[0]}

        # Score distribution tiers
        high_score = db.query(Lead).filter(Lead.score >= 75).count()
        med_score = db.query(Lead).filter(Lead.score >= 50, Lead.score < 75).count()
        low_score = db.query(Lead).filter(Lead.score < 50).count()
        score_distribution = {"High (>74)": high_score, "Medium (50-74)": med_score, "Low (<50)": low_score}

        # Daily Target Tracker for Today (Asia/Kolkata)
        today_str = get_today_kolkata_str()
        daily_stat = db.query(DailyResearchStat).filter_by(date_str=today_str).first()
        reviewed_today = daily_stat.reviewed_count if daily_stat else 0
        qualified_today = daily_stat.qualified_count if daily_stat else 0
        target_reviewed = settings.daily_review_target
        target_qualified = settings.daily_qualified_target

        rev_pct = round(min(100.0, (reviewed_today / target_reviewed) * 100), 1) if target_reviewed else 0.0
        qual_pct = round(min(100.0, (qualified_today / target_qualified) * 100), 1) if target_qualified else 0.0

        # Recent activities (last 10)
        recent_logs = db.query(ActivityLog).order_by(desc(ActivityLog.timestamp)).limit(10).all()
        recent_activity = [
            {
                "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M"),
                "action": log.action_type,
                "description": log.description,
                "lead_id": log.lead_id
            }
            for log in recent_logs
        ]

        # Google Sheets configuration status
        sheets_configured = bool(settings.google_service_account_file or settings.google_service_account_json)
        sheets_status = "Connected" if sheets_configured else "Not Configured (Operating Locally)"

        reddit_mode = "Active" if settings.reddit_integration_enabled else "Disabled (Awaiting Commercial Approval)"

        return {
            "total_leads": total_leads,
            "qualified_leads": qualified_leads,
            "awaiting_review": awaiting_review,
            "disqualified_leads": disqualified_leads,
            "contacted_leads": contacted_leads,
            "average_score": average_score,
            "daily_target": {
                "date_str": today_str,
                "reviewed_count": reviewed_today,
                "reviewed_target": target_reviewed,
                "qualified_count": qualified_today,
                "qualified_target": target_qualified,
                "reviewed_progress_pct": rev_pct,
                "qualified_progress_pct": qual_pct
            },
            "country_breakdown": country_breakdown,
            "industry_breakdown": industry_breakdown,
            "service_breakdown": service_breakdown,
            "score_distribution": score_distribution,
            "recent_activity": recent_activity,
            "reddit_mode": reddit_mode,
            "sheets_status": sheets_status
        }
