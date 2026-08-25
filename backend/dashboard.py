from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from courses import DIFFICULTIES, get_or_create_enrollment, level_complete
from models import Certificate, Course, ExamAttempt, db, to_utc_iso

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.get("")
@jwt_required()
def get_dashboard():
    user_id = int(get_jwt_identity())
    courses = Course.query.order_by(Course.id).all()

    certified_course_ids = {
        row.course_id for row in Certificate.query.filter_by(user_id=user_id).all()
    }

    per_course = []
    levels_completed_total = 0
    for course in courses:
        enrollment = get_or_create_enrollment(user_id, course.id)
        levels = {d: level_complete(user_id, course.id, d, enrollment.cycle_started_at) for d in DIFFICULTIES}
        done_count = sum(levels.values())
        levels_completed_total += done_count
        certified = course.id in certified_course_ids
        pct = 100 if certified else round((done_count / len(DIFFICULTIES)) * 100)
        per_course.append(
            {
                "course_id": course.id,
                "title": course.title,
                "pct": pct,
                "certified": certified,
            }
        )

    certificates = (
        Certificate.query.filter_by(user_id=user_id).order_by(Certificate.issued_at.desc()).all()
    )
    course_titles = {c.id: c.title for c in courses}
    cert_list = [
        {
            "course_id": cert.course_id,
            "title": course_titles.get(cert.course_id, "Unknown course"),
            "cert_id": cert.cert_id,
            "issued_at": to_utc_iso(cert.issued_at),
        }
        for cert in certificates
    ]

    attempts = (
        ExamAttempt.query.filter(ExamAttempt.user_id == user_id, ExamAttempt.status == "completed")
        .order_by(ExamAttempt.started_at.desc())
        .limit(20)
        .all()
    )
    exam_history = [
        {
            "course_title": course_titles.get(a.course_id, "Unknown course"),
            "started_at": to_utc_iso(a.started_at),
            "score": a.score,
            "verdict": a.verdict,
        }
        for a in attempts
    ]

    return jsonify(
        {
            "stats": {
                "certificates_earned": len(certified_course_ids),
                "total_courses": len(courses),
                "levels_completed": levels_completed_total,
                "total_levels": len(courses) * len(DIFFICULTIES),
                "exam_attempts": ExamAttempt.query.filter_by(user_id=user_id, status="completed").count(),
            },
            "courses": per_course,
            "certificates": cert_list,
            "exam_history": exam_history,
        }
    )
