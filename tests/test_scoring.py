import pytest
from scoring import (
    calculate_lead_score,
    detect_matching_service,
    detect_industry,
    detect_country
)
from response_generator import generate_personalized_response

def test_service_detection():
    # Missed calls -> AI Receptionist
    srv, kws = detect_matching_service("We are losing clients because our staff misses incoming phone calls after hours.")
    assert "Receptionist" in srv or "Voice Agent" in srv
    assert "missed call" in kws or "phone calls" in kws

    # Appointment booking
    srv, _ = detect_matching_service("Our clinic is drowning in scheduling appointments and dealing with no-show bookings.")
    assert "Appointment Booking" in srv

    # Repetitive inquiries
    srv, _ = detect_matching_service("We get 100s of unanswered enquiries and repetitive questions on our website every day.")
    assert "Chatbot" in srv or "Enquiry" in srv

def test_industry_detection():
    ind, confirmed = detect_industry("Looking for advice for our private dental practice and clinic operations.")
    assert ind == "Dental Practice"
    assert confirmed is True

    ind2, confirmed2 = detect_industry("Our restaurant catering team has trouble tracking orders.")
    assert ind2 == "Restaurant / Catering"
    assert confirmed2 is True

def test_country_detection():
    cntry, confirmed = detect_country("Based in London, UK, running a property management firm.")
    assert cntry == "United Kingdom"
    assert confirmed is True

    cntry2, confirmed2 = detect_country("Our clinic in Bengaluru, India needs workflow improvements.")
    assert cntry2 == "India"
    assert confirmed2 is True

def test_scoring_system_high_quality():
    title = "Dental practice in Toronto missing 20+ calls daily, losing patients"
    problem = (
        "We run a busy dental clinic in Canada. Our front desk staff is overwhelmed during peak hours and "
        "we are missing incoming phone calls and booking requests from new patients. We need software or an automated "
        "receptionist system to answer calls and schedule appointments automatically."
    )
    score_data = calculate_lead_score(
        title=title,
        problem_text=problem,
        industry="Dental Practice",
        country="Canada",
        matching_service="AI Receptionist / Voice Agent"
    )

    assert score_data["total_score"] >= 70
    assert score_data["recommended_status"] == "Qualified"
    assert len(score_data["reasons"]) > 0
    assert score_data["clarity_score"] > 0
    assert score_data["relevance_score"] >= 20

def test_scoring_system_low_quality():
    title = "Random question"
    problem = "Hello, what is AI?"
    score_data = calculate_lead_score(
        title=title,
        problem_text=problem,
        industry="SMB / General",
        country="Unknown",
        matching_service="Business Workflow Automation"
    )

    assert score_data["total_score"] < 50
    assert score_data["recommended_status"] == "Disqualified"

def test_consultative_response_generation():
    draft = generate_personalized_response(
        title="Can't keep up with customer messages",
        problem_text="Our clinic gets overwhelmed with repetitive questions about hours and pricing.",
        industry="Clinic / Healthcare",
        matching_service="Customer Enquiry Handling / Chatbot",
        author="DrSmith"
    )

    assert "Hi DrSmith," in draft
    assert "FAQ and intake chatbot" in draft
    assert "Happy to share" in draft
    # Check that there are no pushy spam terms
    assert "BUY NOW" not in draft
    assert "EXCLUSIVE OFFER" not in draft
