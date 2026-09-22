
import pytest

from app import create_app, db
from app.models import Application


@pytest.fixture()
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
    })

    with app.app_context():
        db.drop_all()
        db.create_all()

    with app.test_client() as client:
        yield client

    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_create_application(client):
    response = client.post(
        "/api/applications",
        json={
            "company": "Prodesk",
            "role": "Python Developer",
            "location": "Noida",
        },
    )

    assert response.status_code == 201
    assert response.json["company"] == "Prodesk"
    assert response.json["status"] == "Applied"


def test_get_applications(client):
    client.post(
        "/api/applications",
        json={
            "company": "Prodesk",
            "role": "Python Developer",
        },
    )

    response = client.get("/api/applications")

    assert response.status_code == 200
    assert response.json["count"] == 1


def test_update_application(client):
    created = client.post(
        "/api/applications",
        json={
            "company": "Prodesk",
            "role": "Python Developer",
        },
    )

    application_id = created.json["id"]

    response = client.put(
        f"/api/applications/{application_id}",
        json={"status": "Interview"},
    )

    assert response.status_code == 200
    assert response.json["status"] == "Interview"


def test_delete_application(client):
    created = client.post(
        "/api/applications",
        json={
            "company": "Prodesk",
            "role": "Python Developer",
        },
    )

    application_id = created.json["id"]

    response = client.delete(
        f"/api/applications/{application_id}"
    )

    assert response.status_code == 200

    missing = client.get(
        f"/api/applications/{application_id}"
    )

    assert missing.status_code == 404


def test_invalid_application(client):
    response = client.post(
        "/api/applications",
        json={"company": "", "role": "Python Developer"},
    )

    assert response.status_code == 400
    
def test_invalid_status_type(client):
    response = client.post(
        "/api/applications",
        json={
            "company": "Google",
            "role": "Python Developer",
            "status": ["Applied"]
        }
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid status"
    
def test_update_invalid_status_type(client):
    create_response = client.post(
        "/api/applications",
        json={
            "company": "Google",
            "role": "Python Developer"
        }
    )

    application_id = create_response.get_json()["id"]

    response = client.put(
        f"/api/applications/{application_id}",
        json={"status": ["Applied"]}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid status"
    
def test_pagination(client):
    for i in range(3):
        client.post(
            "/api/applications",
            json={
                "company": f"Company {i}",
                "role": "Python Developer"
            }
        )

    response = client.get(
        "/api/applications?page=1&per_page=2"
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert data["total"] == 3
    assert data["total_pages"] == 2
    assert data["count"] == 2
    
def test_pagination_second_page(client):
    for i in range(3):
        client.post(
            "/api/applications",
            json={
                "company": f"Company {i}",
                "role": "Python Developer"
            }
        )

    response = client.get(
        "/api/applications?page=2&per_page=2"
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["page"] == 2
    assert data["count"] == 1
    assert data["total"] == 3
    assert data["total_pages"] == 2
    
def test_pagination_with_status_filter(client):
    client.post(
        "/api/applications",
        json={"company": "Company A", "role": "Developer", "status": "Applied"}
    )
    client.post(
        "/api/applications",
        json={"company": "Company B", "role": "Developer", "status": "Rejected"}
    )
    client.post(
        "/api/applications",
        json={"company": "Company C", "role": "Developer", "status": "Applied"}
    )

    response = client.get(
        "/api/applications?status=Applied&page=1&per_page=1"
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["total"] == 2
    assert data["count"] == 1
    assert data["page"] == 1
    assert data["total_pages"] == 2
    assert data["applications"][0]["status"] == "Applied"
    
def test_invalid_pagination_parameters(client):
    response = client.get(
        "/api/applications?page=abc&per_page=10"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "page and per_page must be integers"
    )
    
def test_pagination_per_page_over_limit(client):
    response = client.get(
        "/api/applications?page=1&per_page=101"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "per_page cannot exceed 100"
    )