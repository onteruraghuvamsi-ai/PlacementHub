# PlacementHub — Job Application Tracker API

A RESTful API built with Python and Flask to help users track job applications, manage application statuses, search opportunities, and view application statistics.

## Features

* Create, view, update, and delete job applications (CRUD).
* Search applications by company, role, or location.
* Filter applications by status and location.
* View application statistics.
* Fetch organization information using the GitHub API.
* Handle external API errors and timeouts.
* Automated API testing using pytest.

## Tech Stack

* **Language:** Python
* **Framework:** Flask
* **Database:** SQLite
* **ORM:** Flask-SQLAlchemy
* **HTTP Requests:** Requests
* **Environment Variables:** python-dotenv
* **Testing:** pytest

## Project Structure

```text
PlacementHub/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   └── services.py
├── tests/
│   └── test_api.py
├── run.py
├── requirements.txt
├── .gitignore
├── README.md
├── manual_request.py
└── manual_advanced.py
```

## Getting Started

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd PlacementHub
```

### 2. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python run.py
```

The API runs locally at:

`http://127.0.0.1:5000`

## API Endpoints

Base URL: `/api/applications`

| Method | Endpoint                              | Description                           |
| ------ | ------------------------------------- | ------------------------------------- |
| GET    | `/api/applications`                   | Get all applications                  |
| POST   | `/api/applications`                   | Create an application                 |
| GET    | `/api/applications/<id>`              | Get one application                   |
| PUT    | `/api/applications/<id>`              | Update an application                 |
| DELETE | `/api/applications/<id>`              | Delete an application                 |
| GET    | `/api/applications/search?q=<term>`   | Search applications                   |
| GET    | `/api/applications/stats`             | Get application statistics            |
| GET    | `/api/applications/github/<org_name>` | Fetch GitHub organization information |

## Running Tests

Run the automated test suite:

```bash
python -m pytest -v
```

## External API

PlacementHub integrates with the GitHub Organizations API to retrieve public organization information.

Example:

`GET /api/applications/github/<org_name>`

## Future Improvements

* Add user authentication.
* Add pagination and sorting.
* Deploy the API to a cloud platform.
* Add a frontend dashboard.
* Support reminders and application deadlines.

## Author

Developed as a Python backend project to demonstrate REST API development, database integration, external API usage, and automated testing.
