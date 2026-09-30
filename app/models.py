from datetime import datetime, timezone
from app import db

class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    case_code_hash = db.Column(db.String(128), unique=True, nullable=False, index=True)
    category = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text, nullable=False)
    evidence_url = db.Column(db.String(2048), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="SUBMITTED")
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                            onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    updates = db.relationship(
        "StatusUpdate", backref="report", lazy=True,
        cascade="all, delete-orphan", order_by="StatusUpdate.created_at"
    )

class StatusUpdate(db.Model):
    __tablename__ = "status_updates"

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("reports.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class Moderator(db.Model):
    __tablename__ = "moderators"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
