from flask import Blueprint, jsonify, request
import traceback
from app.services.database_service import sync_remoteok_jobs
from app.services.database_service import get_jobs_payload
from app.services.database_service import sync_simplify_jobs
from app.services.resume_service import score_resume_against_jobs, get_display_jobs_for_resume

#a simple blueprint for a route to check rest connection health

database_bp = Blueprint("database", __name__)

# Call to get jobs on db
@database_bp.route("/jobs", methods=["GET"])
def jobs():
    try:
        payload, status_code = get_jobs_payload(request.args.get("limit"))
        return jsonify(payload), status_code
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@database_bp.route("/sync/remoteok", methods=["POST"])
def sync_remoteok() -> tuple:
    """
    Sync RemoteOK jobs:
    - Upsert jobs seen now
    - Mark jobs inactive if not seen for N days (default 10)
    """
    limit_raw = request.args.get("limit", "1000")
    days_raw = request.args.get("inactive_after_days", "10")

    try:
        limit = int(limit_raw)
        inactive_days = int(days_raw)
    except ValueError:
        return jsonify({"status": "error", "message": "limit and inactive_after_days must be integers"}), 400

    limit = max(1, min(limit, 2000))
    inactive_days = max(1, min(inactive_days, 365))

    try:
        stats = sync_remoteok_jobs(limit=limit, inactive_after_days=inactive_days)
        return jsonify({"status": "ok", "source": "remoteok", **stats}), 200
    except Exception as e:
        traceback.print_exc()
        return (
            jsonify(
                {
                    "status": "error",
                    "source": "remoteok",
                    "message": str(e)
                }
            ),
            500,
        )
    
@database_bp.route("/sync/simplify", methods=["POST"])
def sync_simplify() -> tuple:
    limit_raw = request.args.get("limit", "1000")
    days_raw = request.args.get("inactive_after_days", "10")

    try:
        limit = int(limit_raw)
        inactive_days = int(days_raw)
    except ValueError:
        return jsonify({"status": "error", "message": "limit and inactive_after_days must be integers"}), 400

    limit = max(1, min(limit, 50000))
    inactive_days = max(1, min(inactive_days, 365))

    stats = sync_simplify_jobs(limit=limit, inactive_after_days=inactive_days)
    return jsonify({"status": "ok", "source": "simplify_newgrad", **stats}), 200


@database_bp.route("/resumes/<int:resume_id>/score", methods=["POST"])
def score_resume(resume_id: int) -> tuple:
    # Trigger scoring for one resume against active jobs.
    try:
        stats = score_resume_against_jobs(resume_id)
        return jsonify({"status": "ok", **stats}), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception:
        return jsonify({"status": "error", "message": "failed to score resume"}), 500


@database_bp.route("/resumes/<int:resume_id>/matches", methods=["GET"])
def get_resume_matches(resume_id: int) -> tuple:
    # Return top matched jobs for a resume.
    limit_raw = request.args.get("limit", "10")
    try:
        limit = int(limit_raw)
    except ValueError:
        return jsonify({"status": "error", "message": "limit must be an integer"}), 400

    try:
        matches = get_display_jobs_for_resume(resume_id=resume_id, limit=limit)
        return jsonify({"status": "ok", "resume_id": resume_id, "count": len(matches), "jobs": matches}), 200
    except Exception:
        return jsonify({"status": "error", "message": "failed to fetch matches"}), 500
