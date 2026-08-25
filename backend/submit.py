import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from judge import ExecutionError, evaluate_against_test_cases
from models import Course, Problem, Submission, db

submit_bp = Blueprint("submit", __name__, url_prefix="/api")


@submit_bp.post("/submit")
@jwt_required()
def submit():
    data = request.get_json(silent=True) or {}
    problem_id = data.get("problem_id")
    code = data.get("code") or ""

    if not problem_id or not code.strip():
        return jsonify({"error": "problem_id and code are required"}), 400

    problem = db.session.get(Problem, problem_id)
    if not problem:
        return jsonify({"error": "problem not found"}), 404

    course = db.session.get(Course, problem.course_id)
    language = course.key

    test_cases = json.loads(problem.test_cases)

    try:
        result = evaluate_against_test_cases(code, test_cases, language=language)
    except ExecutionError as exc:
        return jsonify({"error": str(exc)}), 502

    user_id = int(get_jwt_identity())
    submission = Submission(
        user_id=user_id,
        problem_id=problem.id,
        language=language,
        code=code,
        verdict=result["verdict"],
        score=result["score"],
    )
    db.session.add(submission)
    db.session.commit()

    return jsonify(result)
