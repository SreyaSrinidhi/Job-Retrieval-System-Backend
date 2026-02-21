from flask import Blueprint, jsonify, request
from psycopg.rows import dict_row
from app.extensions import extensions

#a simple blueprint for a route to check rest connection health

database_bp = Blueprint("database", __name__)

# Call to get jobs on db
@database_bp.route("/jobs", methods=["GET"])
def list_jobs():    #TODO - refactor processing and db call out to services layer
    limit = request.args.get("limit", default=10, type=int)
    limit = max(1, min(limit, 50))

    with extensions.get_db_pool().connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, title, company, location, url, description, source, created_at
                FROM jobs
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()

    for r in rows:
        if r["created_at"]:
            r["created_at"] = r["created_at"].isoformat()

    return jsonify({"count": len(rows), "jobs": rows})