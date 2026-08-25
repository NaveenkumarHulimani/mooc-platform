import json
import random
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from courses import DIFFICULTIES, get_or_create_enrollment, level_complete
from judge import ExecutionError, evaluate_against_test_cases
from models import Course, ExamAnswer, ExamAttempt, Problem, db, to_utc_iso

exam_bp = Blueprint("exam", __name__, url_prefix="/api/exam")

EXAM_QUESTION_COUNT = 3
EXAM_DURATION_SECONDS = 15 * 60
PASS_THRESHOLD = 60
LATE_GRACE_SECONDS = 10


def _previously_used_problem_ids(user_id: int, course_id: int) -> set[int]:
    attempts = ExamAttempt.query.filter_by(user_id=user_id, course_id=course_id).all()
    used = set()
    for attempt in attempts:
        used.update(json.loads(attempt.question_ids))
    return used


def _is_expired(attempt: ExamAttempt) -> bool:
    deadline = attempt.started_at.replace(tzinfo=timezone.utc) + timedelta(
        seconds=attempt.duration_seconds + LATE_GRACE_SECONDS
    )
    return datetime.now(timezone.utc) > deadline


def _expire(attempt: ExamAttempt) -> None:
    attempt.status = "expired"
    attempt.score = 0
    attempt.verdict = "FAIL"
    db.session.commit()


def _serialize_attempt(attempt: ExamAttempt) -> dict:
    question_ids = json.loads(attempt.question_ids)
    problems = {p.id: p for p in Problem.query.filter(Problem.id.in_(question_ids)).all()}
    return {
        "attempt_id": attempt.id,
        "course_id": attempt.course_id,
        "started_at": to_utc_iso(attempt.started_at),
        "duration_seconds": attempt.duration_seconds,
        "questions": [
            {
                "id": pid,
                "title": problems[pid].title,
                "difficulty": problems[pid].difficulty,
                "description": problems[pid].description,
                "starter_code": problems[pid].starter_code,
            }
            for pid in question_ids
            if pid in problems
        ],
    }


def _active_attempt_or_none(user_id: int, course_id: int) -> ExamAttempt | None:
    """Returns the user's live in-progress attempt for this course, auto-expiring it
    first if it's past its deadline."""
    attempt = ExamAttempt.query.filter_by(user_id=user_id, course_id=course_id, status="in_progress").first()
    if not attempt:
        return None
    if _is_expired(attempt):
        _expire(attempt)
        return None
    return attempt


def _pick_questions(user_id: int, course_id: int) -> list[Problem]:
    all_problems = Problem.query.filter_by(course_id=course_id).all()
    used_ids = _previously_used_problem_ids(user_id, course_id)
    fresh_pool = [p for p in all_problems if p.id not in used_ids]

    pool = fresh_pool if len(fresh_pool) >= EXAM_QUESTION_COUNT else all_problems

    by_difficulty = {"easy": [], "medium": [], "hard": []}
    for p in pool:
        by_difficulty.setdefault(p.difficulty, []).append(p)

    chosen = []
    for level in ("easy", "medium", "hard"):
        if by_difficulty[level]:
            chosen.append(random.choice(by_difficulty[level]))

    remaining = [p for p in pool if p not in chosen]
    random.shuffle(remaining)
    while len(chosen) < EXAM_QUESTION_COUNT and remaining:
        chosen.append(remaining.pop())

    return chosen[:EXAM_QUESTION_COUNT]


@exam_bp.get("/current")
@jwt_required()
def current_exam():
    """Lets the frontend resume an in-progress exam after navigating away and back,
    instead of it being orphaned server-side with no way to get back in."""
    user_id = int(get_jwt_identity())
    course_id = request.args.get("course_id", type=int)
    if not course_id:
        return jsonify({"error": "course_id is required"}), 400
    attempt = _active_attempt_or_none(user_id, course_id)
    return jsonify({"attempt": _serialize_attempt(attempt) if attempt else None})


@exam_bp.post("/start")
@jwt_required()
def start_exam():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    course_id = data.get("course_id")
    if not course_id:
        return jsonify({"error": "course_id is required"}), 400

    course = db.session.get(Course, course_id)
    if not course:
        return jsonify({"error": "course not found"}), 404

    existing = _active_attempt_or_none(user_id, course_id)
    if existing:
        # Still genuinely active — resume it instead of erroring, so the "Start Exam"
        # button always works whether this is a fresh start or a return visit.
        return jsonify(_serialize_attempt(existing))

    enrollment = get_or_create_enrollment(user_id, course_id)
    if not all(level_complete(user_id, course_id, d, enrollment.cycle_started_at) for d in DIFFICULTIES):
        return jsonify({"error": "Complete Easy, Medium and Hard practice levels before taking the exam."}), 403

    questions = _pick_questions(user_id, course_id)
    if not questions:
        return jsonify({"error": "No problems available to build an exam."}), 400

    attempt = ExamAttempt(
        user_id=user_id,
        course_id=course_id,
        question_ids=json.dumps([p.id for p in questions]),
        duration_seconds=EXAM_DURATION_SECONDS,
        status="in_progress",
    )
    db.session.add(attempt)
    db.session.commit()

    return jsonify(_serialize_attempt(attempt))


@exam_bp.post("/<int:attempt_id>/finalize")
@jwt_required()
def finalize_exam(attempt_id: int):
    user_id = int(get_jwt_identity())
    attempt = db.session.get(ExamAttempt, attempt_id)

    if not attempt or attempt.user_id != user_id:
        return jsonify({"error": "exam attempt not found"}), 404
    if attempt.status != "in_progress":
        return jsonify({"error": "this exam attempt is already finalized"}), 409

    if _is_expired(attempt):
        _expire(attempt)
        _reset_course_cycle(user_id, attempt.course_id)
        return jsonify({"verdict": "FAIL", "score": 0, "expired": True, "per_question": []})

    data = request.get_json(silent=True) or {}
    answers = data.get("answers") or []
    question_ids = set(json.loads(attempt.question_ids))

    per_question = []
    scores = []
    for answer in answers:
        problem_id = answer.get("problem_id")
        if problem_id not in question_ids:
            continue
        code = answer.get("code") or ""
        problem = db.session.get(Problem, problem_id)
        if not problem or not code.strip():
            per_question.append({"problem_id": problem_id, "verdict": "FAIL", "score": 0})
            scores.append(0)
            continue

        language = db.session.get(Course, problem.course_id).key
        test_cases = json.loads(problem.test_cases)
        try:
            result = evaluate_against_test_cases(code, test_cases, language=language)
        except ExecutionError as exc:
            return jsonify({"error": str(exc)}), 502

        db.session.add(
            ExamAnswer(
                attempt_id=attempt.id,
                problem_id=problem_id,
                language=language,
                code=code,
                verdict=result["verdict"],
                score=result["score"],
            )
        )
        per_question.append(
            {"problem_id": problem_id, "title": problem.title, "verdict": result["verdict"], "score": result["score"]}
        )
        scores.append(result["score"])

    overall_score = round(sum(scores) / len(scores)) if scores else 0
    overall_verdict = "PASS" if overall_score >= PASS_THRESHOLD else "FAIL"

    attempt.status = "completed"
    attempt.score = overall_score
    attempt.verdict = overall_verdict
    db.session.commit()

    if overall_verdict == "FAIL":
        _reset_course_cycle(user_id, attempt.course_id)

    return jsonify({"verdict": overall_verdict, "score": overall_score, "per_question": per_question})


def _reset_course_cycle(user_id: int, course_id: int) -> None:
    """Failing the exam resets level-completion for this course: bump the enrollment's
    cycle start so every prior PASS submission stops counting toward the levels,
    without deleting any Submission history."""
    enrollment = get_or_create_enrollment(user_id, course_id)
    enrollment.cycle_started_at = datetime.now(timezone.utc)
    db.session.commit()
