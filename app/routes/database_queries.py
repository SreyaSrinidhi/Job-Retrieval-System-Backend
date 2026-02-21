from flask import Blueprint, jsonify, request
from app.services.database_service import list_jobs

#a simple blueprint for a route to check rest connection health

database_bp = Blueprint("database", __name__)

# Call to get jobs on db
@database_bp.route("/jobs", methods=["GET"])
def jobs():    #TODO - refactor processing and db call out to services layer
    limit = request.args.get("limit", default=10, type=int)
    
    jobs = list_jobs(limit)

    return jsonify({"count": len(jobs), "jobs": jobs})