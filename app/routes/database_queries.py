from flask import Blueprint, jsonify, request
from app.services import database_service

database_bp = Blueprint("database", __name__)

# Call to get jobs on db
#TODO - add error handling / failure capture info
@database_bp.route("/jobs", methods=["GET"])
def jobs():    #TODO - refactor processing and db call out to services layer
    limit = request.args.get("limit", default=10, type=int)
    
    jobs = database_service.list_jobs(limit)

    return jsonify({"count": len(jobs), "jobs": jobs})