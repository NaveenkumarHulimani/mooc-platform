import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

load_dotenv()

from models import db  # noqa: E402
from auth import auth_bp  # noqa: E402
from courses import courses_bp  # noqa: E402
from problems import problems_bp  # noqa: E402
from submit import submit_bp  # noqa: E402
from dashboard import dashboard_bp  # noqa: E402
from ai import ai_bp  # noqa: E402
from exam import exam_bp  # noqa: E402
from certificate import certificate_bp  # noqa: E402
from admin import init_admin  # noqa: E402


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mooc.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-me")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-admin-session-secret-change-me")

    CORS(app)
    db.init_app(app)
    JWTManager(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(problems_bp)
    app.register_blueprint(submit_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(exam_bp)
    app.register_blueprint(certificate_bp)
    init_admin(app)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    # use_reloader=False: this folder is under OneDrive sync, whose periodic mtime
    # touches were spuriously triggering Werkzeug's stat reloader, spawning a
    # growing chain of stale worker processes that intermittently served requests
    # with an outdated environment (e.g. missing .env changes). Restart manually
    # after backend edits instead.
    app.run(debug=True, port=5000, use_reloader=False)
