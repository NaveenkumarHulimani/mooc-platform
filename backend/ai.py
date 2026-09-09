import os

import requests
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from models import Problem, db

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

STUB_MESSAGE = (
    "AI hints aren't configured yet. Add a GEMINI_API_KEY to backend/.env to enable "
    "real hints from an LLM. For now: re-read the problem statement and check your "
    "output format against the examples exactly (whitespace, line breaks, etc.)."
)

GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


@ai_bp.post("/hint")
@jwt_required()
def get_hint():
    data = request.get_json(silent=True) or {}
    problem_id = data.get("problem_id")
    code = data.get("code") or ""

    problem = db.session.get(Problem, problem_id) if problem_id else None
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return jsonify({"hint": STUB_MESSAGE, "source": "stub"})

    prompt = (
        "You are a coding tutor. A student is working on this problem:\n\n"
        f"{problem.description if problem else '(unknown problem)'}\n\n"
        f"Their current code:\n{code}\n\n"
        "Give ONE short hint (2-3 sentences) that nudges them toward the fix "
        "without giving away the full solution or writing corrected code for them."
    )

    try:
        resp = requests.post(
            GEMINI_URL,
            headers={"x-goog-api-key": api_key, "content-type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=20,
        )
        resp.raise_for_status()
        payload = resp.json()
        hint = payload["candidates"][0]["content"]["parts"][0]["text"].strip()
        return jsonify({"hint": hint, "source": "gemini"})
    except Exception as exc:
        print(f"[ai.hint] Gemini request failed: {exc}")
        return jsonify({"hint": STUB_MESSAGE, "source": "stub"})
