
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