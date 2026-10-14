import re
from typing import Dict, Any, Tuple, List

# Core Auyvra service mapping keywords
SERVICE_KEYWORDS = {
    "AI Receptionist / Voice Agent": [
        "missed call", "phone calls", "receptionist", "answering calls", "call volume",
        "after hours calls", "busy phone", "on hold", "front desk", "call answering", "voice bot"
    ],
    "Automated Appointment Booking": [
        "booking", "appointment", "schedule", "scheduling", "calendar", "no-show",
        "rescheduling", "double booked", "consultation booking", "availability"
    ],
    "Customer Enquiry Handling / Chatbot": [
        "unanswered enquiries", "inquiries", "customer support", "slow response", "faq",
        "ticket overload", "live chat", "website visitor", "dm response", "repetitive questions"
    ],
    "Follow-up Automation": [
        "lead follow up", "ghosting", "cold leads", "follow up", "nurturing",
        "email drip", "sms reminder", "pipeline", "lost leads"
    ],
    "Business Workflow Automation": [
        "manual data entry", "repetitive tasks", "admin work", "copy pasting", "zapier",
        "crm sync", "paperwork", "invoice processing", "bottleneck", "inefficient"
    ],
    "AI Lead Generation & Qualification": [
        "qualifying leads", "lead gen", "unqualified inquiries", "tire kickers", "prospecting"
    ]
}

INDUSTRY_PATTERNS = {
    "Dental Practice": [r"\bdental\b", r"\bdentist\b", r"\borthodont\w*\b", r"\bteeth\b"],
    "Clinic / Healthcare": [r"\bclinic\b", r"\bdoctor\b", r"\bphysiotherapy\b", r"\bmedspa\b", r"\bhealth\b", r"\bpatient\b"],
    "Restaurant / Catering": [r"\brestaurant\b", r"\bcatering\b", r"\bcafe\b", r"\bbakery\b", r"\bfood service\b", r"\bdining\b"],
    "Real Estate": [r"\breal estate\b", r"\brealtor\b", r"\bbroker\b", r"\bproperty management\b", r"\blandlord\b", r"\btenant\b"],
    "Home Services": [r"\bhvac\b", r"\bplumb\w*\b", r"\belectric\w*\b", r"\broof\w*\b", r"\blandscap\w*\b", r"\bcontractor\b"],
    "Agency": [r"\bagency\b", r"\bmarketing agency\b", r"\bclient onboarding\b", r"\bdev shop\b"],
    "Professional Services": [r"\baccounting\b", r"\bcpa\b", r"\blaw firm\b", r"\blegal\b", r"\bconsulting\b", r"\badvisory\b"],
    "SMB / General": [r"\bsmall business\b", r"\bmy business\b", r"\bour company\b", r"\bowner\b", r"\bstore\b"]
}

COUNTRY_KEYWORDS = {
    "India": ["india", "inr", "delhi", "mumbai", "bangalore", "bengaluru", "hyderabad", "chennai", "pune"],
    "United States": ["usa", "united states", "us", "usd", "california", "texas", "florida", "new york", "america"],
    "Canada": ["canada", "canadian", "cad", "ontario", "toronto", "vancouver"],
    "United Kingdom": ["uk", "united kingdom", "britain", "gbp", "london", "england", "scotland"],
    "Australia": ["australia", "aussie", "aud", "sydney", "melbourne", "brisbane"],
    "New Zealand": ["new zealand", "nz", "nzd", "auckland", "wellington"],
    "Ireland": ["ireland", "irish", "dublin"],
    "Germany": ["germany", "german", "berlin", "munich"],
    "France": ["france", "french", "paris"],
    "Netherlands": ["netherlands", "dutch", "amsterdam"],
    "Spain": ["spain", "spanish", "madrid", "barcelona"],
    "Switzerland": ["switzerland", "swiss", "zurich", "geneva"],
    "Sweden": ["sweden", "swedish", "stockholm"],
    "Norway": ["norway", "norwegian", "oslo"],
    "Denmark": ["denmark", "danish", "copenhagen"]
}

def detect_matching_service(text: str) -> Tuple[str, List[str]]:
    text_lower = text.lower()
    matched_services = []
    
    for service, keywords in SERVICE_KEYWORDS.items():
        found = [kw for kw in keywords if kw in text_lower]
        if found:
            matched_services.append((service, len(found), found))
            
    if not matched_services:
        return "Business Workflow Automation", ["General business workflow improvement"]
        
    # Sort by number of matched keywords descending
    matched_services.sort(key=lambda x: x[1], reverse=True)
    best_service = matched_services[0][0]
    evidences = matched_services[0][2]
    return best_service, evidences

def detect_industry(text: str) -> Tuple[str, bool]:
    text_lower = text.lower()
    for industry, patterns in INDUSTRY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                return industry, True
    return "SMB / General", False

def detect_country(text: str) -> Tuple[str, bool]:
    text_lower = text.lower()
    for country, keywords in COUNTRY_KEYWORDS.items():
        for kw in keywords:
            # Word boundary search for short codes like us, uk, nz
            if re.search(rf"\b{kw}\b", text_lower):
                return country, True
    return "Unknown", False

def calculate_lead_score(
    title: str,
    problem_text: str,
    industry: str,
    country: str,
    matching_service: str
) -> Dict[str, Any]:
    """
    Transparent 0-100 Lead Scoring System:
    - Clarity of stated problem (0-25)
    - Relevance to Auyvra services (0-30)
    - Evidence of real business need / scale (0-25)
    - Next-step feasibility & outreach potential (0-20)
    """
    combined_text = f"{title} {problem_text}".lower()
    reasons = []

    # 1. Clarity of problem (0 - 25)
    clarity_score = 0
    word_count = len(problem_text.split())
    if word_count >= 30:
        clarity_score += 15
        reasons.append(f"+15: Well-articulated problem description ({word_count} words)")
    elif word_count >= 10:
        clarity_score += 10
        reasons.append(f"+10: Concise problem description ({word_count} words)")
    else:
        clarity_score += 5
        reasons.append("+5: Brief or limited problem description")

    # Specific operational pain points mentioned
    pain_points = [
        "missed", "losing clients", "overwhelmed", "repetitive", "slow", 
        "manual", "too many", "cannot keep up", "no time", "frustrated", "falling behind"
    ]
    matched_pains = [p for p in pain_points if p in combined_text]
    if len(matched_pains) >= 2:
        clarity_score += 10
        reasons.append(f"+10: Specific operational friction terms identified ({', '.join(matched_pains[:3])})")
    elif len(matched_pains) == 1:
        clarity_score += 5
        reasons.append(f"+5: Operational friction term identified ({matched_pains[0]})")
    clarity_score = min(clarity_score, 25)

    # 2. Relevance to Auyvra Services (0 - 30)
    relevance_score = 0
    service_match_keywords = SERVICE_KEYWORDS.get(matching_service, [])
    matched_kws = [kw for kw in service_match_keywords if kw in combined_text]
    
    if len(matched_kws) >= 3:
        relevance_score = 30
        reasons.append(f"+30: Exceptional service alignment with '{matching_service}' (matched: {', '.join(matched_kws[:3])})")
    elif len(matched_kws) >= 1:
        relevance_score = 22
        reasons.append(f"+22: Strong alignment with '{matching_service}' (matched: {', '.join(matched_kws)})")
    else:
        relevance_score = 12
        reasons.append(f"+12: Moderate alignment with Auyvra automation solutions")

    # 3. Evidence of Real Business Need / Commercial Reality (0 - 25)
    business_score = 0
    commercial_signals = [
        "clients", "customers", "patients", "orders", "staff", "employees",
        "revenue", "sales", "invoices", "business", "clinic", "practice", "agency"
    ]
    found_signals = [s for s in commercial_signals if s in combined_text]
    
    if len(found_signals) >= 3:
        business_score += 15
        reasons.append(f"+15: High commercial intent with active operational signals ({', '.join(found_signals[:3])})")
    elif len(found_signals) >= 1:
        business_score += 10
        reasons.append(f"+10: Commercial intent signals detected ({', '.join(found_signals)})")
    else:
        business_score += 4
        reasons.append("+4: Limited commercial signals; could be solo project or consumer")

    if industry and industry != "SMB / General":
        business_score += 10
        reasons.append(f"+10: Target high-value vertical identified ({industry})")
    else:
        business_score += 5
        reasons.append("+5: General business category")
    business_score = min(business_score, 25)

    # 4. Next-Step Feasibility (0 - 20)
    feasibility_score = 0
    # Clear questions, looking for recommendations, or advice seeking
    actionable_prompts = [
        "how do you", "recommend", "advice", "what tool", "anyone using",
        "software", "solution", "automate", "system", "help", "suggestions"
    ]
    matched_actionable = [a for a in actionable_prompts if a in combined_text]
    if matched_actionable:
        feasibility_score += 12
        reasons.append(f"+12: Explicitly seeking recommendations or advice ({', '.join(matched_actionable[:2])})")
    else:
        feasibility_score += 6
        reasons.append("+6: General discussion; conversational entry point required")

    if country and country != "Unknown":
        feasibility_score += 8
        reasons.append(f"+8: Clear geographic context ({country}) enabling timezone-aligned follow-up")
    else:
        feasibility_score += 4
        reasons.append("+4: Unknown geographic origin")
    feasibility_score = min(feasibility_score, 20)

    # Total Calculation
    total_score = clarity_score + relevance_score + business_score + feasibility_score
    total_score = max(0, min(100, total_score))

    # Recommended qualification tier
    if total_score >= 70:
        recommended_status = "Qualified"
    elif total_score >= 45:
        recommended_status = "Awaiting Review"
    else:
        recommended_status = "Disqualified"

    return {
        "total_score": total_score,
        "clarity_score": clarity_score,
        "relevance_score": relevance_score,
        "business_score": business_score,
        "feasibility_score": feasibility_score,
        "reasons": reasons,
        "recommended_status": recommended_status
    }
