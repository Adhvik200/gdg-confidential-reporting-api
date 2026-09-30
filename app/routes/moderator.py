from flask import Blueprint, request
from flask_jwt_extended import create_access_token, jwt_required
from sqlalchemy import select
from werkzeug.security import check_password_hash

from app import db
from app.models import Moderator, Report, StatusUpdate
from app.schemas import CATEGORIES, STATUSES
from app.utils import serialize_moderator_report


moderator_bp = Blueprint("moderator", __name__)


ALLOWED_TRANSITIONS = {
    "SUBMITTED": {"UNDER_REVIEW"},
    "UNDER_REVIEW": {"RESOLVED", "DISMISSED"},
    "RESOLVED": set(),
    "DISMISSED": set(),
}


@moderator_bp.post("/login")
def login():
    """
    Moderator login.
    ---
    tags:
      - Moderator
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
            - username
            - password
          properties:
            username:
              type: string
              example: Adhvik
            password:
              type: string
              format: password
              example: Admin@12345
    responses:
      200:
        description: Successful login.
        schema:
          type: object
          properties:
            access_token:
              type: string
              example: eyJhbGciOiJIUzI1NiIs...
            token_type:
              type: string
              example: Bearer
      400:
        description: Missing or invalid request body.
      401:
        description: Invalid credentials.
    """

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "JSON body required."}, 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {"error": "username and password are required."}, 400

    moderator = db.session.scalar(
        select(Moderator).where(Moderator.username == username)
    )

    if not moderator or not check_password_hash(
        moderator.password_hash,
        password
    ):
        return {"error": "Invalid credentials."}, 401

    token = create_access_token(identity=str(moderator.id))

    return {
        "access_token": token,
        "token_type": "Bearer"
    }, 200


@moderator_bp.get("/reports")
@jwt_required()
def list_reports():
    """
    List and filter reports.
    ---
    tags:
      - Moderator
    produces:
      - application/json
    security:
      - Bearer: []
    parameters:
      - name: category
        in: query
        required: false
        type: string
        enum:
          - Security
          - Harassment
          - Corruption
          - Technical
          - Other
        description: Filter reports by category.
      - name: status
        in: query
        required: false
        type: string
        enum:
          - SUBMITTED
          - UNDER_REVIEW
          - RESOLVED
          - DISMISSED
        description: Filter reports by status.
    responses:
      200:
        description: List of reports.
      400:
        description: Invalid category or status.
      401:
        description: Missing or invalid authentication token.
    """

    category = request.args.get("category")
    status = request.args.get("status")

    if category and category not in CATEGORIES:
        return {"error": "Invalid category."}, 400

    if status and status not in STATUSES:
        return {"error": "Invalid status."}, 400

    query = select(Report).order_by(Report.created_at.desc())

    if category:
        query = query.where(Report.category == category)

    if status:
        query = query.where(Report.status == status)

    reports = db.session.scalars(query).all()

    return {
        "reports": [
            serialize_moderator_report(report)
            for report in reports
        ]
    }, 200


@moderator_bp.get("/reports/<int:report_id>")
@jwt_required()
def get_report(report_id):
    """
    Get a single report by ID.
    ---
    tags:
      - Moderator
    produces:
      - application/json
    security:
      - Bearer: []
    parameters:
      - name: report_id
        in: path
        required: true
        type: integer
        description: ID of the report.
        example: 1
    responses:
      200:
        description: Report details.
      401:
        description: Missing or invalid authentication token.
      404:
        description: Report not found.
    """

    report = db.session.get(Report, report_id)

    if not report:
        return {"error": "Report not found."}, 404

    return serialize_moderator_report(report), 200


@moderator_bp.patch("/reports/<int:report_id>/status")
@jwt_required()
def update_status(report_id):
    """
    Update the status of a report.
    ---
    tags:
      - Moderator
    consumes:
      - application/json
    produces:
      - application/json
    security:
      - Bearer: []
    parameters:
      - name: report_id
        in: path
        required: true
        type: integer
        description: ID of the report.
        example: 1
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - status
            - message
          properties:
            status:
              type: string
              enum:
                - UNDER_REVIEW
                - RESOLVED
                - DISMISSED
              example: UNDER_REVIEW
            message:
              type: string
              example: The report is currently being reviewed.
    responses:
      200:
        description: Report status updated successfully.
      400:
        description: Invalid request data.
      401:
        description: Missing or invalid authentication token.
      404:
        description: Report not found.
      409:
        description: Invalid status transition.
    """

    report = db.session.get(Report, report_id)

    if not report:
        return {"error": "Report not found."}, 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "JSON body required."}, 400

    new_status = data.get("status")
    message = data.get("message")

    if new_status not in STATUSES:
        return {"error": "Invalid status."}, 400

    if new_status not in ALLOWED_TRANSITIONS[report.status]:
        return {
            "error": (
                f"Invalid status transition: "
                f"{report.status} -> {new_status}."
            )
        }, 409

    if not isinstance(message, str) or not message.strip():
        return {
            "error": "A non-empty status update message is required."
        }, 400

    if len(message.strip()) > 1000:
        return {
            "error": "Status update message must not exceed 1000 characters."
        }, 400

    report.status = new_status

    update = StatusUpdate(
        report_id=report.id,
        status=new_status,
        message=message.strip()
    )

    db.session.add(update)
    db.session.commit()

    return {
        "message": "Report status updated successfully.",
        "report": serialize_moderator_report(report)
    }, 200


@moderator_bp.post("/reports/<int:report_id>/updates")
@jwt_required()
def add_update(report_id):
    """
    Add a status update to a report.
    ---
    tags:
      - Moderator
    consumes:
      - application/json
    produces:
      - application/json
    security:
      - Bearer: []
    parameters:
      - name: report_id
        in: path
        required: true
        type: integer
        description: ID of the report.
        example: 1
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - message
          properties:
            message:
              type: string
              example: The relevant information is being verified.
    responses:
      201:
        description: Status update added successfully.
      400:
        description: Invalid request data.
      401:
        description: Missing or invalid authentication token.
      404:
        description: Report not found.
    """

    report = db.session.get(Report, report_id)

    if not report:
        return {"error": "Report not found."}, 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "JSON body required."}, 400

    message = data.get("message")

    if not isinstance(message, str) or not message.strip():
        return {"error": "message is required."}, 400

    if len(message.strip()) > 1000:
        return {
            "error": "message must not exceed 1000 characters."
        }, 400

    update = StatusUpdate(
        report_id=report.id,
        status=report.status,
        message=message.strip()
    )

    db.session.add(update)
    db.session.commit()

    return {
        "message": "Status update added successfully.",
        "status": report.status,
        "update": {
            "status": update.status,
            "message": update.message,
            "created_at": update.created_at.isoformat()
        }
    }, 201