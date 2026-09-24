
import pytest

from app import create_app, db
from app.models import Application, User
from flask_jwt_extended import create_access_token

import requests
from unittest.mock import patch, Mock

from app.services import get_github_organization


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
        with app.app_context():
            user = User(
                username="testuser",
                email="test@example.com"
            )
            user.set_password("TestPass123!")

            db.session.add(user)
            db.session.commit()

            token = create_access_token(
                identity=str(user.id)
            )

        client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"

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
    


def test_create_and_get_interview(client):
    created = client.post(
        "/api/applications",
        json={
            "company": "Google",
            "role": "Python Developer"
        }
    )

    application_id = created.json["id"]

    response = client.post(
        f"/api/applications/{application_id}/interviews",
        json={
            "round_type": "Technical Interview",
            "interview_date": "2026-09-25",
            "notes": "Prepare Python and SQL"
        }
    )

    assert response.status_code == 201

    # Interview data is nested inside "interview".
    interview_data = response.json["interview"]

    assert interview_data["round_type"] == "Technical Interview"
    assert interview_data["interview_date"] == "2026-09-25"

    get_response = client.get(
        f"/api/applications/{application_id}/interviews"
    )

    assert get_response.status_code == 200

    interviews = get_response.json["interviews"]

    assert len(interviews) == 1
    assert interviews[0]["round_type"] == "Technical Interview"


def test_update_interview(client):
    created = client.post(
        "/api/applications",
        json={
            "company": "Google",
            "role": "Python Developer"
        }
    )

    application_id = created.json["id"]

    interview = client.post(
        f"/api/applications/{application_id}/interviews",
        json={
            "round_type": "Technical Interview"
        }
    )

    interview_id = interview.json["interview"]["id"]

    response = client.put(
        f"/api/applications/{application_id}/interviews/{interview_id}",
        json={
            "round_type": "Final Interview",
            "interview_date": "2026-09-28",
            "notes": "Final discussion"
        }
    )

    assert response.status_code == 200

    interview_data = response.json["interview"]

    assert interview_data["round_type"] == "Final Interview"
    assert interview_data["interview_date"] == "2026-09-28"
    assert interview_data["notes"] == "Final discussion"


def test_delete_interview(client):
    created = client.post(
        "/api/applications",
        json={
            "company": "Google",
            "role": "Python Developer"
        }
    )

    application_id = created.json["id"]

    interview = client.post(
        f"/api/applications/{application_id}/interviews",
        json={
            "round_type": "HR Interview"
        }
    )

    interview_id = interview.json["interview"]["id"]

    response = client.delete(
        f"/api/applications/{application_id}/interviews/{interview_id}"
    )

    assert response.status_code == 200

    get_response = client.get(
        f"/api/applications/{application_id}/interviews"
    )

    assert get_response.status_code == 200
    assert get_response.json["interviews"] == []


def test_interviews_for_missing_application(client):
    response = client.get(
        "/api/applications/9999/interviews"
    )

    assert response.status_code == 404
    

def test_create_interview_with_invalid_date(client):
    created = client.post(
        "/api/applications",
        json={
            "company": "Google",
            "role": "Python Developer"
        }
    )

    application_id = created.json["id"]

    response = client.post(
        f"/api/applications/{application_id}/interviews",
        json={
            "round_type": "Technical Interview",
            "interview_date": "not-a-date"
        }
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        "interview_date must be a valid YYYY-MM-DD date"
    )


def test_update_missing_interview(client):
    created = client.post(
        "/api/applications",
        json={
            "company": "Google",
            "role": "Python Developer"
        }
    )

    application_id = created.json["id"]

    response = client.put(
        f"/api/applications/{application_id}/interviews/9999",
        json={
            "round_type": "Final Interview"
        }
    )

    assert response.status_code == 404
    assert response.json["error"] == "Interview round not found"


def test_interview_cannot_be_updated_under_wrong_application(client):
    first_app = client.post(
        "/api/applications",
        json={
            "company": "Google",
            "role": "Python Developer"
        }
    )

    second_app = client.post(
        "/api/applications",
        json={
            "company": "Microsoft",
            "role": "Software Engineer"
        }
    )

    first_id = first_app.json["id"]
    second_id = second_app.json["id"]

    interview_response = client.post(
        f"/api/applications/{first_id}/interviews",
        json={
            "round_type": "Technical Interview"
        }
    )

    interview_id = interview_response.json["interview"]["id"]

    response = client.put(
        f"/api/applications/{second_id}/interviews/{interview_id}",
        json={
            "round_type": "Final Interview"
        }
    )

    assert response.status_code == 404
    assert response.json["error"] == "Interview round not found"
    
def test_create_interview_with_non_string_round_type(client):
    app_response = client.post("/api/applications", json={
        "company": "Google",
        "role": "Python Developer"
    })
    app_id = app_response.json["id"]

    response = client.post(
        f"/api/applications/{app_id}/interviews",
        json={"round_type": 123}
    )

    assert response.status_code == 400
    assert response.json["error"] == "round_type must be a non-empty string"


def test_update_interview_with_non_string_notes(client):
    app_response = client.post("/api/applications", json={
        "company": "Google",
        "role": "Python Developer"
    })
    app_id = app_response.json["id"]

    interview_response = client.post(
        f"/api/applications/{app_id}/interviews",
        json={"round_type": "Technical"}
    )
    interview_id = interview_response.json["interview"]["id"]

    response = client.put(
        f"/api/applications/{app_id}/interviews/{interview_id}",
        json={"notes": 123}
    )

    assert response.status_code == 400
def test_create_interview_with_non_string_notes(client):
    app_response = client.post(
        "/api/applications",
        json={
            "company": "Google",
            "role": "Python Developer",
        },
    )

    assert app_response.status_code == 201
    app_id = app_response.json["id"]

    response = client.post(
        f"/api/applications/{app_id}/interviews",
        json={
            "round_type": "Technical",
            "notes": 123,
        },
    )

    assert response.status_code == 400
    assert response.json["error"] == "notes must be a string or null"
    
def test_create_interview_with_malformed_json(client):
    app_response = client.post(
        "/api/applications",
        json={
            "company": "Google",
            "role": "Python Developer"
        }
    )
    app_id = app_response.json["id"]

    response = client.post(
        f"/api/applications/{app_id}/interviews",
        data='{"round_type":',
        content_type="application/json"
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        "Request body must be a JSON object"
    )


def test_update_interview_with_malformed_json(client):
    app_response = client.post(
        "/api/applications",
        json={
            "company": "Google",
            "role": "Python Developer"
        }
    )
    app_id = app_response.json["id"]

    interview_response = client.post(
        f"/api/applications/{app_id}/interviews",
        json={"round_type": "Technical"}
    )
    interview_id = interview_response.json["interview"]["id"]

    response = client.put(
        f"/api/applications/{app_id}/interviews/{interview_id}",
        data='{"round_type":',
        content_type="application/json"
    )

    assert response.status_code == 400
    assert response.json["error"] == (
        "Request body must be a JSON object"
    )

def test_search_applications_by_company(client):
    client.post("/api/applications", json={
        "company": "Google",
        "role": "Software Engineer"
    })
    client.post("/api/applications", json={
        "company": "Amazon",
        "role": "Developer"
    })

    response = client.get("/api/applications?search=Google")

    assert response.status_code == 200
    data = response.get_json()

    assert data["total"] == 1
    assert data["applications"][0]["company"] == "Google"
    
def test_search_applications_by_role(client):
    client.post("/api/applications", json={
        "company": "Google",
        "role": "Data Analyst"
    })
    client.post("/api/applications", json={
        "company": "Amazon",
        "role": "Software Engineer"
    })

    response = client.get("/api/applications?search=Data")

    assert response.status_code == 200
    data = response.get_json()

    assert data["total"] == 1
    assert data["applications"][0]["role"] == "Data Analyst"
    
def test_filter_applications_by_location(client):
    client.post("/api/applications", json={
        "company": "Google",
        "role": "Developer",
        "location": "Hyderabad"
    })
    client.post("/api/applications", json={
        "company": "Amazon",
        "role": "Developer",
        "location": "Bangalore"
    })

    response = client.get("/api/applications?location=Hyderabad")

    assert response.status_code == 200
    data = response.get_json()

    assert data["total"] == 1
    assert data["applications"][0]["location"] == "Hyderabad"
    
def test_combined_search_status_location_filters(client):
    # Matching application
    client.post("/api/applications", json={
        "company": "Google",
        "role": "Data Analyst",
        "location": "Hyderabad",
        "status": "Applied"
    })

    # Wrong location
    client.post("/api/applications", json={
        "company": "Google",
        "role": "Data Analyst",
        "location": "Bangalore",
        "status": "Applied"
    })

    # Wrong status
    client.post("/api/applications", json={
        "company": "Google",
        "role": "Data Analyst",
        "location": "Hyderabad",
        "status": "Interview"
    })

    # Wrong company/role search term
    client.post("/api/applications", json={
        "company": "Amazon",
        "role": "Developer",
        "location": "Hyderabad",
        "status": "Applied"
    })

    response = client.get(
        "/api/applications"
        "?search=Google"
        "&status=Applied"
        "&location=Hyderabad"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["total"] == 1
    assert data["count"] == 1
    assert data["applications"][0]["company"] == "Google"
    assert data["applications"][0]["location"] == "Hyderabad"
    assert data["applications"][0]["status"] == "Applied"
    
def test_applications_page_beyond_results(client):
    client.post("/api/applications", json={
        "company": "Google",
        "role": "Developer"
    })

    response = client.get(
        "/api/applications?page=5&per_page=10"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 0
    assert data["total"] == 1
    assert data["page"] == 5
    assert data["applications"] == []
    assert data["total_pages"] == 1
    
def test_invalid_pagination_parameters(client):
    test_cases = [
        ("?page=abc", 400),
        ("?per_page=abc", 400),
        ("?page=0", 400),
        ("?per_page=0", 400),
        ("?per_page=101", 400),
    ]

    for query, expected_status in test_cases:
        response = client.get(
            f"/api/applications{query}"
        )

        assert response.status_code == expected_status
        
def test_invalid_status_filter(client):
    response = client.get(
        "/api/applications?status=NotARealStatus"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid status filter"
    
def test_search_is_case_insensitive(client):
    client.post("/api/applications", json={
        "company": "Google",
        "role": "Software Engineer"
    })

    response = client.get(
        "/api/applications?search=google"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["total"] == 1
    assert data["applications"][0]["company"] == "Google"
    
def test_applications_pagination_has_no_duplicates(client):
    for i in range(5):
        response = client.post("/api/applications", json={
            "company": f"Company{i}",
            "role": "Developer"
        })
        assert response.status_code in (200, 201)

    page1 = client.get("/api/applications?page=1&per_page=2").get_json()
    page2 = client.get("/api/applications?page=2&per_page=2").get_json()
    page3 = client.get("/api/applications?page=3&per_page=2").get_json()

    assert page1["count"] == 2
    assert page2["count"] == 2
    assert page3["count"] == 1

    ids = (
        [app["id"] for app in page1["applications"]]
        + [app["id"] for app in page2["applications"]]
        + [app["id"] for app in page3["applications"]]
    )

    assert len(ids) == 5
    assert len(set(ids)) == 5
    
def test_get_applications_when_empty(client):
    response = client.get("/api/applications")

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 0
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["per_page"] == 10
    assert data["total_pages"] == 0
    assert data["applications"] == []
    
def test_search_strips_surrounding_whitespace(client):
    client.post("/api/applications", json={
        "company": "Google",
        "role": "Software Engineer"
    })

    response = client.get(
        "/api/applications?search=%20%20Google%20%20"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["total"] == 1
    assert data["applications"][0]["company"] == "Google"

def test_get_applications_sort_by_company(client):
    client.post("/api/applications", json={
        "company": "Zebra",
        "role": "Developer"
    })
    client.post("/api/applications", json={
        "company": "Apple",
        "role": "Developer"
    })

    response = client.get(
        "/api/applications?sort_by=company&order=asc"
    )

    assert response.status_code == 200
    data = response.get_json()

    companies = [
        app["company"] for app in data["applications"]
    ]

    assert companies == ["Apple", "Zebra"]


def test_get_applications_sort_by_company_desc(client):
    client.post("/api/applications", json={
        "company": "Apple",
        "role": "Developer"
    })
    client.post("/api/applications", json={
        "company": "Zebra",
        "role": "Developer"
    })

    response = client.get(
        "/api/applications?sort_by=company&order=desc"
    )

    assert response.status_code == 200
    data = response.get_json()

    companies = [
        app["company"] for app in data["applications"]
    ]

    assert companies == ["Zebra", "Apple"]
    
def test_get_applications_invalid_sort_by(client):
    response = client.get(
        "/api/applications?sort_by=password"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid sort_by field"


def test_get_applications_invalid_sort_order(client):
    response = client.get(
        "/api/applications?sort_by=company&order=sideways"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid sort order" 

def test_statistics_when_empty(client):
    response = client.get("/api/applications/stats")

    assert response.status_code == 200

    data = response.get_json()

    assert data["total_applications"] == 0
    assert data["status_counts"] == {}
    
def test_statistics_counts_by_status(client):
    # Create 3 applications with different statuses
    client.post("/api/applications", json={
        "company": "Google",
        "role": "Developer",
        "status": "Applied"
    })

    client.post("/api/applications", json={
        "company": "Amazon",
        "role": "Analyst",
        "status": "Applied"
    })

    client.post("/api/applications", json={
        "company": "Microsoft",
        "role": "Engineer",
        "status": "Interview"
    })

    response = client.get("/api/applications/stats")

    assert response.status_code == 200

    data = response.get_json()

    assert data["total_applications"] == 3
    assert data["status_counts"] == {
        "Applied": 2,
        "Interview": 1
    }
    
from unittest.mock import patch


def test_github_organization_success(client):
    mock_data = {
        "name": "OpenAI",
        "login": "openai",
        "description": "AI research and deployment",
        "public_repositories": 100,
        "website": "https://openai.com",
        "location": "San Francisco",
        "github_url": "https://github.com/openai"
    }

    with patch(
        "app.routes.get_github_organization",
        return_value=(mock_data, 200)
    ):
        response = client.get("/api/applications/github/openai")

    assert response.status_code == 200
    assert response.get_json() == mock_data


def test_github_organization_not_found(client):
    mock_data = {
        "error": "GitHub organization not found"
    }

    with patch(
        "app.routes.get_github_organization",
        return_value=(mock_data, 404)
    ):
        response = client.get(
            "/api/applications/github/unknown-org"
        )

    assert response.status_code == 404
    assert response.get_json() == mock_data


def test_github_organization_timeout(client):
    mock_data = {
        "error": "GitHub API request timed out"
    }

    with patch(
        "app.routes.get_github_organization",
        return_value=(mock_data, 504)
    ):
        response = client.get(
            "/api/applications/github/openai"
        )

    assert response.status_code == 504
    assert response.get_json() == mock_data
    
@patch("app.services.requests.get")
def test_github_service_success(mock_get):
    mock_response = Mock()

    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "OpenAI",
        "login": "openai",
        "description": "AI research",
        "public_repos": 50,
        "blog": "https://openai.com",
        "location": "San Francisco",
        "html_url": "https://github.com/openai"
    }

    mock_get.return_value = mock_response

    result, status_code = get_github_organization("openai")

    assert status_code == 200
    assert result["name"] == "OpenAI"
    assert result["login"] == "openai"
    assert result["public_repositories"] == 50

    mock_get.assert_called_once_with(
        "https://api.github.com/orgs/openai",
        timeout=5,
        headers={"Accept": "application/vnd.github+json"}
    )
    
@patch("app.services.requests.get")
def test_github_service_not_found(mock_get):
    mock_response = Mock()
    mock_response.status_code = 404

    mock_get.return_value = mock_response

    result, status_code = get_github_organization("unknown-org")

    assert status_code == 404
    assert result == {
        "error": "GitHub organization not found"
    }
    
@patch("app.services.requests.get")
def test_github_service_timeout(mock_get):
    mock_get.side_effect = requests.Timeout

    result, status_code = get_github_organization("openai")

    assert status_code == 504
    assert result == {
        "error": "GitHub API request timed out"
    }
    
@patch("app.services.requests.get")
def test_github_service_request_error(mock_get):
    mock_get.side_effect = requests.RequestException

    result, status_code = get_github_organization("openai")

    assert status_code == 502
    assert result == {
        "error": "Unable to retrieve organization details"
    }