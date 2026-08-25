import os

import requests
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from models import Problem

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

STUB_MESSAGE = (
    "AI hints aren't configured yet. Add an OPENAI_API_KEY to backend/.env to enable "
    "real hints from an LLM. For now: re-read the problem statement and check your "
    "output format against the examples exactly (whitespace, line breaks, etc.)."
)


@ai_bp.post("/hint")
@jwt_required()
def get_hint():
    data = request.get_json(silent=True) or {}
    problem_id = data.get("problem_id")
    code = data.get("code") or ""

    problem = Problem.query.get(problem_id) if problem_id else None
    api_key = os.environ.get("OPENAI_API_KEY")

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
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "content-type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150,
            },
            timeout=20,
        )
        resp.raise_for_status()
        hint = resp.json()["choices"][0]["message"]["content"].strip()
        return jsonify({"hint": hint, "source": "openai"})
    except Exception:
        return jsonify({"hint": STUB_MESSAGE, "source": "stub"})
