import os
import time

import requests
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from models import Problem, db

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

NOT_CONFIGURED_MESSAGE = (
    "AI hints aren't configured yet. Add a GEMINI_API_KEY to backend/.env to enable "
    "real hints from an LLM. For now: re-read the problem statement and check your "
    "output format against the examples exactly (whitespace, line breaks, etc.)."
)
RATE_LIMITED_MESSAGE = (
    "The AI hint service is rate-limited right now (too many requests to the free "
    "Gemini API key). Wait a bit and try again. For now: re-read the problem "
    "statement and check your output format against the examples exactly."
)
UNAVAILABLE_MESSAGE = (
    "Couldn't reach the AI hint service just now. Try again in a moment. For now: "
    "re-read the problem statement and check your output format against the "
    "examples exactly (whitespace, line breaks, etc.)."
)

GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# Gemini intermittently returns 503 under transient server-side load — worth a
# couple of quick retries before giving up. 429 (rate limit) is deliberately NOT
# retried: hammering a rate-limited endpoint again immediately only makes it worse.
MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 0.8
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}


class GeminiError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _call_gemini(api_key: str, prompt: str) -> str:
    last_error = None
    last_status = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = requests.post(
                GEMINI_URL,
                headers={"x-goog-api-key": api_key, "content-type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    # Gemini's "thinking" models otherwise burn the token budget on
                    # internal reasoning parts and can return no visible text part.
                    "generationConfig": {"thinkingConfig": {"thinkingBudget": 0}},
                },
                timeout=20,
            )
            last_status = resp.status_code
            if resp.status_code in RETRYABLE_STATUS_CODES and attempt < MAX_ATTEMPTS:
                last_error = f"{resp.status_code} (attempt {attempt}/{MAX_ATTEMPTS}), retrying"
                time.sleep(RETRY_DELAY_SECONDS)
                continue

            resp.raise_for_status()
            payload = resp.json()

            # A response can contain multiple parts (e.g. a reasoning part with no
            # "text" key followed by the actual answer) — don't assume parts[0] has it.
            parts = payload["candidates"][0]["content"]["parts"]
            hint = next((p["text"] for p in parts if "text" in p), None)
            if not hint:
                raise ValueError(f"no text part in Gemini response: {payload}")
            return hint.strip()
        except requests.exceptions.HTTPError as exc:
            last_error = str(exc)
            last_status = exc.response.status_code if exc.response is not None else last_status
            break
        except (requests.exceptions.RequestException, ValueError, KeyError, IndexError) as exc:
            last_error = str(exc)
            if attempt < MAX_ATTEMPTS:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            break

    raise GeminiError(last_error, status_code=last_status)


@ai_bp.post("/hint")
@jwt_required()
def get_hint():
    data = request.get_json(silent=True) or {}
    problem_id = data.get("problem_id")
    code = data.get("code") or ""

    problem = db.session.get(Problem, problem_id) if problem_id else None
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return jsonify({"hint": NOT_CONFIGURED_MESSAGE, "source": "stub"})

    prompt = (
        "You are a coding tutor. A student is working on this problem:\n\n"
        f"{problem.description if problem else '(unknown problem)'}\n\n"
        f"Their current code:\n{code}\n\n"
        "Give ONE short hint (2-3 sentences) that nudges them toward the fix "
        "without giving away the full solution or writing corrected code for them."
    )

    try:
        hint = _call_gemini(api_key, prompt)
        return jsonify({"hint": hint, "source": "gemini"})
    except GeminiError as exc:
        print(f"[ai.hint] Gemini request failed after retries: {exc}", flush=True)
        message = RATE_LIMITED_MESSAGE if exc.status_code == 429 else UNAVAILABLE_MESSAGE
        return jsonify({"hint": message, "source": "stub"})
