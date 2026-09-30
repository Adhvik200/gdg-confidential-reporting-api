import hashlib
import secrets
import string

ALPHABET = string.ascii_uppercase + string.digits

def generate_case_code():
    # 32 random characters from a CSPRNG; intentionally not derived from DB IDs.
    raw = "".join(secrets.choice(ALPHABET) for _ in range(32))
    return f"GDG-{raw[:8]}-{raw[8:16]}-{raw[16:24]}-{raw[24:]}"

def hash_case_code(case_code):
    return hashlib.sha256(case_code.encode("utf-8")).hexdigest()

def serialize_update(update):
    return {
        "status": update.status,
        "message": update.message,
        "created_at": update.created_at.isoformat()
    }

def serialize_public_report(report, case_code=None):
    data = {
        "status": report.status,
        "category": report.category,
        "created_at": report.created_at.isoformat(),
        "updated_at": report.updated_at.isoformat(),
        "updates": [serialize_update(u) for u in report.updates]
    }
    if case_code:
        data["case_code"] = case_code
    return data

def serialize_moderator_report(report):
    return {
        "id": report.id,
        "category": report.category,
        "description": report.description,
        "evidence_url": report.evidence_url,
        "status": report.status,
        "created_at": report.created_at.isoformat(),
        "updated_at": report.updated_at.isoformat(),
        "updates": [serialize_update(u) for u in report.updates]
    }
