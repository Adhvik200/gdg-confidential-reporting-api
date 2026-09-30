from app import db
from app.models import Moderator
from werkzeug.security import generate_password_hash

def create_moderator(app):
    with app.app_context():
        moderator = Moderator(
            username="admin",
            password_hash=generate_password_hash("password123")
        )
        db.session.add(moderator)
        db.session.commit()

def get_token(client):
    response = client.post("/api/moderator/login", json={
        "username": "admin",
        "password": "password123"
    })
    return response.get_json()["access_token"]

def test_moderator_workflow(app, client):
    create_moderator(app)
    token = get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post("/api/reports", json={
        "category": "Security",
        "description": "Confidential security report."
    })
    assert created.status_code == 201

    reports = client.get("/api/moderator/reports", headers=headers)
    assert reports.status_code == 200
    report = reports.get_json()["reports"][0]
    report_id = report["id"]

    update = client.patch(
        f"/api/moderator/reports/{report_id}/status",
        headers=headers,
        json={"status": "UNDER_REVIEW", "message": "Review started."}
    )
    assert update.status_code == 200

    invalid_transition = client.patch(
    f"/api/moderator/reports/{report_id}/status",
    headers=headers,
    json={"status": "SUBMITTED", "message": "Trying to move the case backwards."}
)
    assert invalid_transition.status_code == 409    
