def test_create_and_track_report(client):
    response = client.post("/api/reports", json={
        "category": "Technical",
        "description": "A confidential technical issue."
    })
    assert response.status_code == 201
    body = response.get_json()
    assert "case_code" in body

    track = client.get(f"/api/reports/track/{body['case_code']}")
    assert track.status_code == 200
    tracked = track.get_json()
    assert tracked["status"] == "SUBMITTED"
    assert tracked["category"] == "Technical"

def test_invalid_case_code(client):
    response = client.get("/api/reports/track/GDG-NOT-A-REAL-CODE")
    assert response.status_code == 404

def test_invalid_category(client):
    response = client.post("/api/reports", json={
        "category": "Invalid",
        "description": "Something"
    })
    assert response.status_code == 400
