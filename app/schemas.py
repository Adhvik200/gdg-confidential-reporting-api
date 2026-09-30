from urllib.parse import urlparse

CATEGORIES = {"Security", "Harassment", "Corruption", "Technical", "Other"}
STATUSES = {"SUBMITTED", "UNDER_REVIEW", "RESOLVED", "DISMISSED"}

def validate_report_payload(data):
    if not isinstance(data, dict):
        return None, {"error": "Request body must be a JSON object."}

    category = data.get("category")
    description = data.get("description")
    evidence_url = data.get("evidence_url")

    if not category:
        return None, {"error": "category is required."}
    if category not in CATEGORIES:
        return None, {"error": f"category must be one of: {', '.join(sorted(CATEGORIES))}."}
    if not isinstance(description, str) or not description.strip():
        return None, {"error": "description is required and must be a non-empty string."}
    if len(description.strip()) > 10000:
        return None, {"error": "description must not exceed 10000 characters."}

    if evidence_url is not None:
        if not isinstance(evidence_url, str) or len(evidence_url) > 2048:
            return None, {"error": "evidence_url must be a valid URL up to 2048 characters."}
        parsed = urlparse(evidence_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None, {"error": "evidence_url must use http or https."}

    return {
        "category": category,
        "description": description.strip(),
        "evidence_url": evidence_url.strip() if isinstance(evidence_url, str) else None
    }, None

def validate_status(status):
    if status not in STATUSES:
        return False
    return True
