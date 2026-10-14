import io
import csv
from typing import Dict, Any, Optional, List, Tuple
from sources.base import BaseLeadSource
from scoring import (
    detect_matching_service,
    detect_industry,
    detect_country,
    calculate_lead_score
)
from response_generator import generate_personalized_response

class ManualLeadSource(BaseLeadSource):
    """
    Primary data ingestion source for Manual Research Mode:
    - Direct URL & detail inputs
    - Freeform discussion notes parser
    - CSV batch file processor with row-by-row validation
    """

    @property
    def source_name(self) -> str:
        return "Manual Research"

    @property
    def is_enabled(self) -> bool:
        return True

    def parse_discussion(self, raw_input: str, url: Optional[str] = None) -> Dict[str, Any]:
        lines = [line.strip() for line in raw_input.strip().splitlines() if line.strip()]
        
        if not lines:
            title = "Manual Research Entry"
            problem_text = raw_input.strip()
        else:
            # First line as title if short, otherwise generate summary
            if len(lines[0]) <= 120:
                title = lines[0]
                problem_text = "\n".join(lines[1:]) if len(lines) > 1 else lines[0]
            else:
                title = lines[0][:100] + "..."
                problem_text = "\n".join(lines)

        industry, ind_found = detect_industry(raw_input)
        country, country_found = detect_country(raw_input)
        matching_service, matched_kws = detect_matching_service(raw_input)

        score_data = calculate_lead_score(
            title=title,
            problem_text=problem_text,
            industry=industry,
            country=country,
            matching_service=matching_service
        )

        response_draft = generate_personalized_response(
            title=title,
            problem_text=problem_text,
            industry=industry,
            matching_service=matching_service,
            author=None
        )

        return {
            "title": title,
            "url": url or "",
            "stated_problem": problem_text,
            "industry": industry,
            "country": country,
            "country_confirmed": country_found,
            "matching_service": matching_service,
            "score": score_data["total_score"],
            "score_breakdown": score_data,
            "suggested_response": response_draft,
            "recommended_status": score_data["recommended_status"],
            "source": "Manual Entry"
        }

    def process_csv(self, csv_content: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Parses and validates CSV content.
        Supports standard columns:
        url, title, stated_problem, industry, country, source, author, notes
        Returns: (valid_records, error_list)
        """
        reader = csv.DictReader(io.StringIO(csv_content))
        valid_records = []
        errors = []

        if not reader.fieldnames:
            return [], ["The uploaded CSV file is empty or missing headers."]

        # Normalize column header names
        normalized_headers = {h.strip().lower().replace(" ", "_"): h for h in reader.fieldnames if h}
        
        # Check required columns (URL and problem or title)
        has_url = "url" in normalized_headers or "discussion_url" in normalized_headers or "link" in normalized_headers
        has_problem = "stated_problem" in normalized_headers or "problem" in normalized_headers or "notes" in normalized_headers or "description" in normalized_headers
        has_title = "title" in normalized_headers or "discussion_title" in normalized_headers

        if not has_url:
            errors.append("CSV Error: Missing required column 'url' or 'discussion_url'.")
            return [], errors

        row_idx = 1
        for row in reader:
            row_idx += 1
            # Retrieve values with flexible header matching
            def get_val(keys: List[str], default: str = "") -> str:
                for k in keys:
                    if k in normalized_headers:
                        val = row.get(normalized_headers[k])
                        if val and val.strip():
                            return val.strip()
                return default

            url = get_val(["url", "discussion_url", "link"])
            title = get_val(["title", "discussion_title", "subject"])
            problem = get_val(["stated_problem", "problem", "notes", "description", "details"])
            industry = get_val(["industry", "category", "business_type"])
            country = get_val(["country", "location", "region"])
            source = get_val(["source", "subreddit", "platform"], default="CSV Import")
            author = get_val(["author", "user", "username"])
            custom_notes = get_val(["notes", "comment", "extra_notes"])

            if not url or not (url.startswith("http://") or url.startswith("https://")):
                errors.append(f"Row {row_idx}: Invalid or missing URL '{url}'.")
                continue

            if not problem and not title:
                errors.append(f"Row {row_idx}: Must provide either a 'title' or 'stated_problem'.")
                continue

            if not title:
                title = problem[:80] + "..." if len(problem) > 80 else problem
            if not problem:
                problem = title

            # Detect defaults if not provided
            if not industry or industry == "SMB / General":
                detected_ind, _ = detect_industry(f"{title} {problem}")
                industry = detected_ind

            country_confirmed = False
            if not country or country == "Unknown":
                detected_cntry, confirmed = detect_country(f"{title} {problem}")
                country = detected_cntry
                country_confirmed = confirmed
            else:
                country_confirmed = True

            matching_service, _ = detect_matching_service(f"{title} {problem}")

            score_data = calculate_lead_score(
                title=title,
                problem_text=problem,
                industry=industry,
                country=country,
                matching_service=matching_service
            )

            suggested_response = generate_personalized_response(
                title=title,
                problem_text=problem,
                industry=industry,
                matching_service=matching_service,
                author=author
            )

            valid_records.append({
                "url": url,
                "title": title,
                "stated_problem": problem,
                "industry": industry,
                "country": country,
                "country_confirmed": country_confirmed,
                "source": source,
                "author": author,
                "matching_service": matching_service,
                "score": score_data["total_score"],
                "score_breakdown": score_data,
                "qualification_status": score_data["recommended_status"],
                "notes": custom_notes,
                "suggested_response": suggested_response
            })

        return valid_records, errors
