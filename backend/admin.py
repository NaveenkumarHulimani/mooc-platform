from flask import Blueprint, redirect, render_template, request, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from models import Certificate, Course, CourseEnrollment, ExamAnswer, ExamAttempt, Problem, Submission, User, db

admin_auth_bp = Blueprint("admin_auth", __name__, url_prefix="/admin")

login_manager = LoginManager()
login_manager.login_view = "admin_auth.login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@admin_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = User.query.filter_by(email=email).first()
        if user and user.is_admin and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(request.args.get("next") or url_for("admin.index"))
        error = "Invalid credentials, or this account is not an admin."
    return render_template("admin_login.html", error=error)


@admin_auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("admin_auth.login"))


class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("admin_auth.login", next=request.url))


class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("admin_auth.login", next=request.url))

    @expose("/")
    def index(self):
        stats = {
            "users": User.query.count(),
            "courses": Course.query.count(),
            "problems": Problem.query.count(),
            "submissions": Submission.query.count(),
            "exam_attempts": ExamAttempt.query.count(),
            "certificates": Certificate.query.count(),
        }
        return self.render("admin_index.html", stats=stats)


class UserAdminView(SecureModelView):
    column_exclude_list = ["password_hash"]
    form_excluded_columns = ["password_hash", "created_at"]
    column_searchable_list = ["name", "email"]


class CourseAdminView(SecureModelView):
    column_list = ["id", "key", "title", "tag"]
    form_columns = ["key", "title", "tag", "description"]
    column_searchable_list = ["title", "key"]


class ProblemAdminView(SecureModelView):
    column_list = ["id", "course", "title", "difficulty"]
    form_columns = ["course", "title", "difficulty", "description", "starter_code", "test_cases"]
    column_searchable_list = ["title"]


class CourseEnrollmentAdminView(SecureModelView):
    column_list = ["id", "user_id", "course_id", "cycle_started_at"]
    can_create = False


class SubmissionAdminView(SecureModelView):
    column_list = ["id", "user_id", "problem_id", "language", "verdict", "score", "created_at"]
    can_create = False
    can_edit = False


class ExamAttemptAdminView(SecureModelView):
    column_list = ["id", "user_id", "course_id", "started_at", "duration_seconds", "status", "score", "verdict"]
    can_create = False
    can_edit = False


class ExamAnswerAdminView(SecureModelView):
    column_list = ["id", "attempt_id", "problem_id", "language", "verdict", "score"]
    can_create = False
    can_edit = False


class CertificateAdminView(SecureModelView):
    column_list = ["id", "user_id", "course_id", "cert_id", "score", "issued_at"]
    can_create = False
    can_edit = False


def init_admin(app):
    login_manager.init_app(app)
    app.register_blueprint(admin_auth_bp)

    admin = Admin(
        app,
        name="MOOC Admin",
        theme=Bootstrap4Theme(),
        index_view=SecureAdminIndexView(url="/admin"),
    )
    admin.add_view(UserAdminView(User, db.session, name="Users", endpoint="admin-users"))
    admin.add_view(CourseAdminView(Course, db.session, name="Courses", endpoint="admin-courses"))
    admin.add_view(ProblemAdminView(Problem, db.session, name="Problems", endpoint="admin-problems"))
    admin.add_view(
        CourseEnrollmentAdminView(
            CourseEnrollment, db.session, name="Course Enrollments", endpoint="admin-enrollments"
        )
    )
    admin.add_view(
        SubmissionAdminView(Submission, db.session, name="Submissions", endpoint="admin-submissions")
    )
    admin.add_view(
        ExamAttemptAdminView(ExamAttempt, db.session, name="Exam Attempts", endpoint="admin-exam-attempts")
    )
    admin.add_view(
        ExamAnswerAdminView(ExamAnswer, db.session, name="Exam Answers", endpoint="admin-exam-answers")
    )
    admin.add_view(
        CertificateAdminView(Certificate, db.session, name="Certificates", endpoint="admin-certificates")
    )
