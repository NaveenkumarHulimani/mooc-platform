from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from certificate_pdf import build_certificate_pdf
from models import Certificate, Course, ExamAttempt, User, db, to_utc_iso

certificate_bp = Blueprint("certificate", __name__, url_prefix="/api/certificate")


def _get_or_create_certificate(user_id: int, course_id: int) -> Certificate | None:
    cert = Certificate.query.filter_by(user_id=user_id, course_id=course_id).first()
    if cert:
        return cert

    passing_attempt = (
        ExamAttempt.query.filter_by(user_id=user_id, course_id=course_id, verdict="PASS")
        .order_by(ExamAttempt.started_at.desc())
        .first()
    )
    if not passing_attempt:
        return None

    cert_id = f"MOOC-2026-{passing_attempt.id:05d}"
    cert = Certificate(
        user_id=user_id,
        course_id=course_id,
        exam_attempt_id=passing_attempt.id,
        cert_id=cert_id,
        score=passing_attempt.score,
    )
    db.session.add(cert)
    db.session.commit()
    return cert


@certificate_bp.get("")
@jwt_required()
def get_certificate():
    user_id = int(get_jwt_identity())
    course_id = request.args.get("course_id", type=int)
    if not course_id:
        return jsonify({"error": "course_id is required"}), 400

    cert = _get_or_create_certificate(user_id, course_id)
    if not cert:
        return jsonify({"has_certificate": False})

    return jsonify(
        {
            "has_certificate": True,
            "cert_id": cert.cert_id,
            "score": cert.score,
            "issued_at": to_utc_iso(cert.issued_at),
        }
    )


@certificate_bp.get("/download")
@jwt_required()
def download_certificate():
    user_id = int(get_jwt_identity())
    course_id = request.args.get("course_id", type=int)
    if not course_id:
        return jsonify({"error": "course_id is required"}), 400

    cert = _get_or_create_certificate(user_id, course_id)
    if not cert:
        return jsonify({"error": "no certificate earned yet"}), 404

    user = db.session.get(User, user_id)
    course = db.session.get(Course, course_id)
    pdf_buffer = build_certificate_pdf(user.name, course.title, cert.score, cert.cert_id, cert.issued_at)

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{cert.cert_id}.pdf",
    )
