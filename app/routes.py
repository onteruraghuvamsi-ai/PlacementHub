from sqlalchemy import select, or_
from flask import Blueprint, request
from sqlalchemy import select
from sqlalchemy import func

from app import db
from app.models import Application, InterviewRound
from datetime import date
from flask import jsonify

applications_bp = Blueprint(
    "applications",
    __name__,
    url_prefix="/api/applications"
)

VALID_STATUSES = {
    "Applied",
    "Shortlisted",
    "Interview",
    "Selected",
    "Rejected"
}


# CREATE
@applications_bp.route("", methods=["POST"])
def create_application():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "Request body must be valid JSON"}, 400

    company = data.get("company")
    role = data.get("role")

    if not isinstance(company, str) or not company.strip():
        return {"error": "Company is required"}, 400

    if not isinstance(role, str) or not role.strip():
        return {"error": "Role is required"}, 400

    status = data.get("status", "Applied")

    if not isinstance(status, str) or status not in VALID_STATUSES:
        return {"error": "Invalid status"}, 400
    
    for field in ("location", "notes"):
        value = data.get(field)

        if value is not None and not isinstance(value, str):
            return {"error": f"{field} must be a string or null"}, 400

    application = Application(
        company=company.strip(),
        role=role.strip(),
        location=data.get("location"),
        status=status,
        notes=data.get("notes")
    )

    db.session.add(application)
    db.session.commit()

    return application.to_dict(), 201

# READ ALL + SEARCH + FILTERING
@applications_bp.route("", methods=["GET"])
def get_applications():
    stmt = select(Application)
    
        # Pagination
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        return {"error": "page and per_page must be integers"}, 400

    if page < 1 or per_page < 1:
        return {"error": "page and per_page must be positive"}, 400

    if per_page > 100:
        return {"error": "per_page cannot exceed 100"}, 400

    # Search by company or role
    search = request.args.get("search", "").strip()

    if search:
        stmt = stmt.where(
            db.or_(
                Application.company.ilike(f"%{search}%"),
                Application.role.ilike(f"%{search}%")
            )
        )

    # Filter by status
    status = request.args.get("status", "").strip()

    if status:
        if status not in VALID_STATUSES:
            return {"error": "Invalid status filter"}, 400

        stmt = stmt.where(Application.status == status)

    # Filter by location
    location = request.args.get("location", "").strip()

    if location:
        stmt = stmt.where(
            Application.location.ilike(f"%{location}%")
        )

        # Total matching applications before pagination
    total = db.session.scalar(
        select(func.count()).select_from(stmt.subquery())
    )

    # Fetch only the requested page
    applications = db.session.execute(
        stmt.order_by(Application.id.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    ).scalars().all()

    return {
        "count": len(applications),
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "applications": [
            application.to_dict()
            for application in applications
        ]
    }


# READ ONE
@applications_bp.route("/<int:application_id>", methods=["GET"])
def get_application(application_id):
    application = db.session.get(Application, application_id)

    if application is None:
        return {"error": "Application not found"}, 404

    return application.to_dict()

# CREATE INTERVIEW ROUND
@applications_bp.route(
    "/<int:application_id>/interviews",
    methods=["POST"]
)
def create_interview(application_id):
    application = db.get_or_404(Application, application_id)

    data = request.get_json()

    # Validate request body
    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be a JSON object"
        }), 400

    # Validate round_type
    round_type = data.get("round_type")

    if not isinstance(round_type, str) or not round_type.strip():
        return jsonify({
            "error": "round_type must be a non-empty string"
        }), 400
        
    notes = data.get("notes")
    
    if notes is not None and not isinstance(notes, str):
            return jsonify({
                "error": "notes must be a string or null"
            }), 400

    round_type = round_type.strip()

    # Validate interview_date
    interview_date = data.get("interview_date")

    if interview_date is not None:
        try:
            interview_date = date.fromisoformat(interview_date)
        except (TypeError, ValueError):
            return jsonify({
                "error": "interview_date must be a valid YYYY-MM-DD date"
            }), 400

    # Create interview
    interview = InterviewRound(
        round_type=round_type,
        interview_date=interview_date,
        notes=notes,
        application_id=application.id
    )

    db.session.add(interview)
    db.session.commit()

    return jsonify({
        "message": "Interview round created successfully",
        "interview": interview.to_dict()
    }), 201
    
# READ INTERVIEW ROUNDS
@applications_bp.route(
    "/<int:application_id>/interviews",
    methods=["GET"]
)
def get_interviews(application_id):
    application = db.session.get(Application, application_id)

    if application is None:
        return {"error": "Application not found"}, 404

    interviews = application.interview_rounds

    return {
        "application_id": application_id,
        "interviews": [
            {
                "id": interview.id,
                "round_type": interview.round_type,
                "interview_date": (
                    interview.interview_date.isoformat()
                    if interview.interview_date else None
                ),
                "notes": interview.notes
            }
            for interview in interviews
        ]
    }, 200
    
# UPDATE INTERVIEW ROUND
@applications_bp.route(
    "/<int:application_id>/interviews/<int:interview_id>",
    methods=["PUT"]
)
def update_interview(application_id, interview_id):
    application = db.get_or_404(Application, application_id)

    interview = InterviewRound.query.filter_by(
        id=interview_id,
        application_id=application.id
    ).first()

    if interview is None:
        return jsonify({
            "error": "Interview round not found"
        }), 404

    data = request.get_json()

    # Validate request body
    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be a JSON object"
        }), 400

    # Update round_type
    if "round_type" in data:
        round_type = data["round_type"]

        if not isinstance(round_type, str) or not round_type.strip():
            return jsonify({
                "error": "round_type must be a non-empty string"
            }), 400

        interview.round_type = round_type.strip()

    # Update interview_date
    if "interview_date" in data:
        interview_date = data["interview_date"]

        if interview_date is None:
            interview.interview_date = None
        else:
            try:
                interview.interview_date = date.fromisoformat(
                    interview_date
                )
            except (TypeError, ValueError):
                return jsonify({
                    "error": "interview_date must be a valid YYYY-MM-DD date"
                }), 400

    # Update notes
    if "notes" in data:
        notes = data["notes"]

        if notes is not None and not isinstance(notes, str):
            return jsonify({
                "error": "notes must be a string or null"
            }), 400

        interview.notes = notes

    db.session.commit()

    return jsonify({
        "message": "Interview round updated successfully",
        "interview": interview.to_dict()
    }), 200
    
# DELETE INTERVIEW ROUND
@applications_bp.route(
    "/<int:application_id>/interviews/<int:interview_id>",
    methods=["DELETE"]
)
def delete_interview(application_id, interview_id):
    application = db.session.get(Application, application_id)

    if application is None:
        return {"error": "Application not found"}, 404

    interview = db.session.get(InterviewRound, interview_id)

    if interview is None or interview.application_id != application_id:
        return {"error": "Interview round not found"}, 404

    db.session.delete(interview)
    db.session.commit()

    return {
        "message": "Interview round deleted successfully"
    }, 200

# UPDATE
@applications_bp.route("/<int:application_id>", methods=["PUT"])
def update_application(application_id):
    application = db.session.get(Application, application_id)

    if application is None:
        return {"error": "Application not found"}, 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "Request body must be valid JSON"}, 400

    if "company" in data:
        if not isinstance(data["company"], str) or not data["company"].strip():
            return {"error": "Company cannot be empty"}, 400
        application.company = data["company"].strip()

    if "role" in data:
        if not isinstance(data["role"], str) or not data["role"].strip():
            return {"error": "Role cannot be empty"}, 400
        application.role = data["role"].strip()

    for field in ("location", "notes"):
        if field in data:
            value = data[field]

            if value is not None and not isinstance(value, str):
                return {"error": f"{field} must be a string or null"}, 400

            setattr(application, field, value)

    if "status" in data:
        if not isinstance(data["status"], str) or data["status"] not in VALID_STATUSES:
            return {"error": "Invalid status"}, 400
        application.status = data["status"]

    db.session.commit()

    return application.to_dict()


# DELETE
@applications_bp.route("/<int:application_id>", methods=["DELETE"])
def delete_application(application_id):
    application = db.session.get(Application, application_id)

    if application is None:
        return {"error": "Application not found"}, 404

    db.session.delete(application)
    db.session.commit()

    return {
        "message": "Application deleted successfully",
        "id": application_id
    }
    
# DASHBOARD STATISTICS
@applications_bp.route("/stats", methods=["GET"])
def get_statistics():
    total = db.session.scalar(
        select(func.count()).select_from(Application)
    )

    status_rows = db.session.execute(
        select(
            Application.status,
            func.count(Application.id)
        ).group_by(Application.status)
    ).all()

    status_counts = {
        status: count
        for status, count in status_rows
    }

    return {
        "total_applications": total,
        "status_counts": status_counts
    }
    
from app.services import get_github_organization


# EXTERNAL API INTEGRATION
@applications_bp.route("/github/<string:org_name>", methods=["GET"])
def github_organization(org_name):
    data, status_code = get_github_organization(org_name)
    return data, status_code

