from flask import Blueprint, jsonify, request
from app.services.database_service import sync_remoteok_jobs
from app.services.database_service import get_jobs_payload
from app.services.database_service import sync_simplify_jobs

#a simple blueprint for a route to check rest connection health

database_bp = Blueprint("database", __name__)

# Call to get jobs on db
#TODO - add error handling / failure capture info
@database_bp.route("/jobs", methods=["GET"])
def jobs():
    payload, status_code = get_jobs_payload(request.args.get("limit"))
    return jsonify(payload), status_code

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
        return (
            jsonify(
                {
                    "status": "error",
                    "source": "remoteok",
                    "message": "failed to sync RemoteOK jobs"
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
