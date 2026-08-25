from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def to_utc_iso(dt: datetime) -> str:
    """SQLite drops tzinfo on datetimes we store as UTC — reattach it before
    serializing, otherwise JS `new Date(...)` parses the string as local time."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(20), unique=True, nullable=False)  # python | java | c
    title = db.Column(db.String(200), nullable=False)
    tag = db.Column(db.String(50), nullable=False, default="Programming")
    description = db.Column(db.Text, nullable=False)


class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # easy | medium | hard
    description = db.Column(db.Text, nullable=False)
    starter_code = db.Column(db.Text, nullable=False)  # plain source snippet in the course's language
    test_cases = db.Column(db.Text, nullable=False)  # JSON string: [{"input": "", "expected_output": ""}]

    course = db.relationship("Course")


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable=False)
    language = db.Column(db.String(20), nullable=False, default="python")
    code = db.Column(db.Text, nullable=False)
    verdict = db.Column(db.String(10), nullable=False)  # PASS | FAIL
    score = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class CourseEnrollment(db.Model):
    """Tracks a per-(user, course) 'cycle' start. Failing that course's exam bumps
    cycle_started_at to now, which makes every prior PASS submission stop counting
    toward level-completion — without deleting any Submission history."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    cycle_started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("user_id", "course_id", name="uq_enrollment_user_course"),)


class ExamAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    question_ids = db.Column(db.Text, nullable=False)  # JSON list of Problem ids
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    duration_seconds = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="in_progress")  # in_progress | completed | expired
    score = db.Column(db.Integer, nullable=True)
    verdict = db.Column(db.String(10), nullable=True)  # PASS | FAIL


class ExamAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("exam_attempt.id"), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey("problem.id"), nullable=False)
    language = db.Column(db.String(20), nullable=False, default="python")
    code = db.Column(db.Text, nullable=False)
    verdict = db.Column(db.String(10), nullable=False)
    score = db.Column(db.Integer, nullable=False, default=0)


class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    exam_attempt_id = db.Column(db.Integer, db.ForeignKey("exam_attempt.id"), nullable=False)
    cert_id = db.Column(db.String(40), unique=True, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    issued_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("user_id", "course_id", name="uq_certificate_user_course"),)
