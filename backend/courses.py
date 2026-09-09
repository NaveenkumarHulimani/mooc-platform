from datetime import datetime, timezone

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import Certificate, Course, CourseEnrollment, Problem, Submission, db

courses_bp = Blueprint("courses", __name__, url_prefix="/api/courses")

DIFFICULTIES = ("easy", "medium", "hard")


def get_or_create_enrollment(user_id: int, course_id: int) -> CourseEnrollment:
    enrollment = CourseEnrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
    if enrollment:
        return enrollment
    enrollment = CourseEnrollment(user_id=user_id, course_id=course_id)
    db.session.add(enrollment)
    db.session.commit()
    return enrollment


def level_complete(user_id: int, course_id: int, difficulty: str, cycle_started_at: datetime) -> bool:
    problem_ids = [
        p.id for p in Problem.query.filter_by(course_id=course_id, difficulty=difficulty).all()
    ]
    if not problem_ids:
        return False

    if cycle_started_at.tzinfo is None:
        cycle_started_at = cycle_started_at.replace(tzinfo=timezone.utc)

    passed_count = (
        db.session.query(Submission.problem_id)
        .filter(
            Submission.user_id == user_id,
            Submission.problem_id.in_(problem_ids),
            Submission.verdict == "PASS",
            Submission.created_at >= cycle_started_at.replace(tzinfo=None),
        )
        .distinct()
        .count()
    )
    return passed_count == len(problem_ids)


def is_level_unlocked(user_id: int, course_id: int, difficulty: str) -> bool:
    """Easy is always open; Medium/Hard require every problem in each preceding
    difficulty to have been solved during the current enrollment cycle."""
    if difficulty not in DIFFICULTIES:
        return False
    idx = DIFFICULTIES.index(difficulty)
    if idx == 0:
        return True
    enrollment = get_or_create_enrollment(user_id, course_id)
    return all(
        level_complete(user_id, course_id, DIFFICULTIES[i], enrollment.cycle_started_at)
        for i in range(idx)
    )


def _serialize_course(course: Course, user_id: int) -> dict:
    enrollment = get_or_create_enrollment(user_id, course.id)
    levels = {d: level_complete(user_id, course.id, d, enrollment.cycle_started_at) for d in DIFFICULTIES}
    all_levels_done = all(levels.values())
    certified = (
        db.session.query(Certificate.id)
        .filter_by(user_id=user_id, course_id=course.id)
        .first()
        is not None
    )
    return {
        "id": course.id,
        "key": course.key,
        "title": course.title,
        "tag": course.tag,
        "description": course.description,
        "levels": levels,
        "all_levels_done": all_levels_done,
        "certified": certified,
    }


@courses_bp.get("")
@jwt_required()
def list_courses():
    user_id = int(get_jwt_identity())
    courses = Course.query.order_by(Course.id).all()
    return jsonify([_serialize_course(c, user_id) for c in courses])


@courses_bp.get("/<int:course_id>")
@jwt_required()
def get_course(course_id: int):
    user_id = int(get_jwt_identity())
    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({"error": "course not found"}), 404
    return jsonify(_serialize_course(course, user_id))
