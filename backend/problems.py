import json

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import Problem, Submission, db

problems_bp = Blueprint("problems", __name__, url_prefix="/api/problems")


def _status_for_user(problem_id: int, user_id: int) -> dict:
    subs = Submission.query.filter_by(problem_id=problem_id, user_id=user_id).all()
    return {
        "attempted": len(subs) > 0,
        "solved": any(s.verdict == "PASS" for s in subs),
    }


def _serialize(problem: Problem, user_id: int | None, include_tests: bool = False) -> dict:
    data = {
        "id": problem.id,
        "course_id": problem.course_id,
        "title": problem.title,
        "difficulty": problem.difficulty,
        "description": problem.description,
        "starter_code": problem.starter_code,
    }
    if user_id is not None:
        data.update(_status_for_user(problem.id, user_id))
    if include_tests:
        data["test_cases"] = json.loads(problem.test_cases)
    return data


@problems_bp.get("")
@jwt_required()
def list_problems():
    user_id = int(get_jwt_identity())
    course_id = request.args.get("course_id", type=int)
    difficulty = request.args.get("difficulty")

    query = Problem.query
    if course_id:
        query = query.filter_by(course_id=course_id)
    if difficulty:
        query = query.filter_by(difficulty=difficulty.lower())

    problems = query.order_by(Problem.id).all()
    return jsonify([_serialize(p, user_id) for p in problems])


@problems_bp.get("/<int:problem_id>")
@jwt_required()
def get_problem(problem_id: int):
    user_id = int(get_jwt_identity())
    problem = db.session.get(Problem, problem_id)
    if not problem:
        return jsonify({"error": "problem not found"}), 404
    return jsonify(_serialize(problem, user_id))
