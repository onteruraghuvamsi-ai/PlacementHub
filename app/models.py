
from datetime import date, datetime, timezone

from app import db


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)

    company = db.Column(
        db.String(100),
        nullable=False
    )

    role = db.Column(
        db.String(100),
        nullable=False
    )

    location = db.Column(
        db.String(100),
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Applied"
    )

    applied_date = db.Column(
        db.Date,
        nullable=False,
        default=date.today
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # One application can have multiple interview rounds.
    interview_rounds = db.relationship(
        "InterviewRound",
        back_populates="application",
        cascade="all, delete-orphan"
    )

    # Convert an Application object into a JSON-friendly dictionary.
    def to_dict(self):
        return {
            "id": self.id,
            "company": self.company,
            "role": self.role,
            "location": self.location,
            "status": self.status,
            "applied_date": (
                self.applied_date.isoformat()
                if self.applied_date
                else None
            ),
            "notes": self.notes,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            )
        }


class InterviewRound(db.Model):
    __tablename__ = "interview_rounds"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    round_type = db.Column(
        db.String(50),
        nullable=False
    )

    interview_date = db.Column(
        db.Date,
        nullable=True
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    application_id = db.Column(
        db.Integer,
        db.ForeignKey("applications.id"),
        nullable=False
    )

    # Connect this interview round to its application.
    application = db.relationship(
        "Application",
        back_populates="interview_rounds"
    )

    # Convert an InterviewRound object into a JSON-friendly dictionary.
    def to_dict(self):
        return {
            "id": self.id,
            "round_type": self.round_type,
            "interview_date": (
                self.interview_date.isoformat()
                if self.interview_date
                else None
            ),
            "notes": self.notes,
            "application_id": self.application_id
        }