
from datetime import date, datetime, timezone

from app import db


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=True)
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
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(
    db.DateTime(timezone=True),
    nullable=False,
    default=lambda: datetime.now(timezone.utc)
)

    def to_dict(self):
        return {
            "id": self.id,
            "company": self.company,
            "role": self.role,
            "location": self.location,
            "status": self.status,
            "applied_date": self.applied_date.isoformat(),
            "notes": self.notes,
            "created_at": self.created_at.isoformat()
        }