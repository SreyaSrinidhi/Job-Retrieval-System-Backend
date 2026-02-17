from flask import Flask, jsonify, request
import os
import psycopg

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello World!"

# DB connection helper
def get_conn():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg.connect(db_url)

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/db-health")
def db_health():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                val = cur.fetchone()[0]

        return jsonify({"status": "ok", "db": "connected", "result": val})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# GET Jobs
@app.route("/jobs", methods=["GET"])
def list_jobs():
    limit = request.args.get("limit", default=10, type=int)
    limit = max(1, min(limit, 50))

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, company, location, url, description, source, created_at
                FROM jobs
                ORDER BY created_at DESC
                LIMIT %s;
                """,
                (limit,),
            )
            rows = cur.fetchall()

    jobs = [
        {
            "id": r[0],
            "title": r[1],
            "company": r[2],
            "location": r[3],
            "url": r[4],
            "description": r[5],
            "source": r[6],
            "created_at": r[7].isoformat() if r[7] else None,
        }
        for r in rows
    ]

    return jsonify({"count": len(jobs), "jobs": jobs})

if __name__ == "__main__":
    app.run(debug=True)   #when running in debug mode, updates will automatically be added to live run of app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)