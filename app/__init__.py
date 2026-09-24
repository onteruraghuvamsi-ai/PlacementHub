
from flask import Flask, app
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from flask_jwt_extended import JWTManager

from dotenv import load_dotenv
import os

load_dotenv()
def create_app(test_config=None):
    app = Flask(__name__)
    
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    jwt = JWTManager(app)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placementhub.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Allow tests to override the database configuration
    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from app.models import Application, InterviewRound, User
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