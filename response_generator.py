from typing import Optional

def generate_personalized_response(
    title: str,
    problem_text: str,
    industry: str,
    matching_service: str,
    author: Optional[str] = None
) -> str:
    """
    Generates a natural, consultative reply draft.
    - Directly addresses the operational challenge
    - Provides actionable, practical advice first
    - Strictly avoids spam, false claims, and aggressive pitching
    - Strictly for human review and approval
    """
    greeting = f"Hi {author}," if author and author.strip() and author.lower() != "unknown" else "Hi there,"

    service_lower = matching_service.lower()
    
    # 1. AI Receptionist / Missed Calls
    if "receptionist" in service_lower or "voice agent" in service_lower or "call" in problem_text.lower():
        advice_body = (
            "Dealing with missed calls while trying to run day-to-day operations is one of the quickest ways "
            "leads fall through the cracks—especially during peak hours or after-hours when prospective clients call around. "
            "\n\nA practical setup that works well is having an intelligent voice assistant or automated call-handling system "
            "that answers immediately when the front desk is tied up, captures the caller's specific inquiry, and instantly sends "
            "an SMS confirmation or calendar link while the lead is still warm. Even a simple triage workflow that logs the caller "
            "and notifies you via Slack/WhatsApp can save hours of phone tag."
        )
    # 2. Automated Appointment Booking
    elif "appointment" in service_lower or "booking" in service_lower or "schedule" in problem_text.lower():
        advice_body = (
            "The back-and-forth email/message dance to schedule consultations or visits creates a lot of friction, "
            "and every additional step drops conversion noticeably. "
            "\n\nIf you haven't already, connecting an automated booking workflow that syncs directly with your team's real-time "
            "calendar and sends automated 24-hour and 2-hour SMS/WhatsApp reminders will cut down both admin time and no-shows significantly. "
            "You can also set automated buffer times between appointments so your schedule doesn't get overloaded."
        )
    # 3. Follow-up Automation
    elif "follow-up" in service_lower or "follow up" in problem_text.lower():
        advice_body = (
            "Most potential clients don't convert on the first touchpoint, and manual follow-ups are usually the first thing "
            "that gets dropped when workload spikes. "
            "\n\nA multi-channel follow-up sequence (a sequence of 2-3 value-focused check-ins across email and SMS spaced 2 to 4 days apart) "
            "often recovers 20-30% of otherwise silent inquiries. The key is making each touchpoint offer something genuinely helpful "
            "(a case study, an answer to a common question, or an easy next step) rather than just 'checking in'."
        )
    # 4. Customer Enquiry Handling / Chatbots
    elif "enquiry" in service_lower or "chatbot" in service_lower or "support" in problem_text.lower():
        advice_body = (
            "Answering the same repetitive questions about pricing, hours, service details, and availability quickly burns team energy. "
            "\n\nA dedicated FAQ and intake chatbot on your primary inquiry channels (website, WhatsApp, or socials) that provides instant, "
            "accurate answers 24/7 can handle 70%+ of routine inquiries right away, while cleanly routing complex inquiries "
            "with full context directly to your inbox or CRM."
        )
    # 5. Business Workflow Automation
    else:
        advice_body = (
            "Repetitive admin tasks and manual data transfers between tools are a silent drain on operational efficiency. "
            "\n\nA clean way to tackle this is identifying the exact handoff points—such as when a new inquiry arrives to when it's entered into "
            "your CRM or spreadsheet—and connecting them with an automated webhook or workflow pipeline. Setting up a structured data flow "
            "eliminates copy-pasting errors and frees your team to focus on high-value client work."
        )

    # Contextual closing
    closing = (
        "\n\nHappy to share how other teams have structured this type of automation pipeline if you'd like to bounce ideas around!"
    )

    draft = f"{greeting}\n\n{advice_body}{closing}"
    return draft
