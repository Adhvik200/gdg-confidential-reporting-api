from flask import Blueprint, request
from sqlalchemy import select

from app import db
from app.models import Report
from app.schemas import validate_report_payload
from app.utils import generate_case_code, hash_case_code, serialize_public_report


reports_bp = Blueprint("reports", __name__)


@reports_bp.post("/reports")
def create_report():
    """
    Create an anonymous report.
    ---
    tags:
      - Reports
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - category
            - description
          properties:
            category:
              type: string
              enum:
                - Security
                - Harassment
                - Corruption
                - Technical
                - Other
              example: Security
            description:
              type: string
              example: I noticed a potential security issue that should be reviewed.
            evidence_url:
              type: string
              nullable: true
              example: https://example.com/evidence
    responses:
      201:
        description: Report submitted successfully.
        schema:
          type: object
          properties:
            message:
              type: string
              example: Report submitted successfully.
            case_code:
              type: string
              example: GDG-748LKQND-JS7J3EOK-41Y34Y5Y-CRZN658F
            status:
              type: string
              example: SUBMITTED
            warning:
              type: string
              example: Keep this case code safe. It is the only way to track this report.
      400:
        description: Invalid report data.
      503:
        description: Could not generate a unique case code.
    """

    data, error = validate_report_payload(request.get_json(silent=True))

    if error:
        return error, 400

    # Extremely unlikely collision; retry if one ever occurs.
    for _ in range(5):
        case_code = generate_case_code()
        case_hash = hash_case_code(case_code)

        if not db.session.scalar(
            select(Report).where(Report.case_code_hash == case_hash)
        ):
            break
    else:
        return {
            "error": "Could not generate a unique case code. Please try again."
        }, 503

    report = Report(
        case_code_hash=case_hash,
        category=data["category"],
        description=data["description"],
        evidence_url=data["evidence_url"],
        status="SUBMITTED",
    )

    db.session.add(report)
    db.session.commit()

    return {
        "message": "Report submitted successfully.",
        "case_code": case_code,
        "status": report.status,
        "warning": "Keep this case code safe. It is the only way to track this report.",
    }, 201


@reports_bp.get("/reports/track/<case_code>")
def track_report(case_code):
    """
    Track an anonymous report using its case code.
    ---
    tags:
      - Reports
    produces:
      - application/json
    parameters:
      - name: case_code
        in: path
        required: true
        type: string
        description: Secret case code received when submitting the report.
        example: GDG-748LKQND-JS7J3EOK-41Y34Y5Y-CRZN658F
    responses:
      200:
        description: Report status and updates.
      400:
        description: Invalid case code format.
      404:
        description: Case code not found.
    """

    if not isinstance(case_code, str) or len(case_code) > 100:
        return {"error": "Invalid case code."}, 400

    report = db.session.scalar(
        select(Report).where(
            Report.case_code_hash == hash_case_code(case_code)
        )
    )

    if not report:
        return {"error": "Invalid case code."}, 404

    return serialize_public_report(report), 200