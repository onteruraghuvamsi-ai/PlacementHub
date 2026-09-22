
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(test_config=None):
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placementhub.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Allow tests to override the database configuration
    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from app.models import Application, InterviewRound
    from app.routes import applications_bp

    app.register_blueprint(applications_bp)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return {
            "message": "Welcome to PlacementHub API!",
            "status": "running"
        }

    return app