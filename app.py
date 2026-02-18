import os
from google import genai
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

app = Flask(__name__)
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

#raise error if no Gemini API key
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

#initialize LLM model
client = genai.Client(api_key=gemini_api_key)

#basic helper function to make llm call
#just returns text back for now
def call_llm(prompt: str) -> str:
    # removed env var check cause we are hard coding for now
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt)

    if not response.text:
        raise ValueError("Empty response from LLM")

    return response.text.strip()

def get_conn():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg.connect(db_url)

@app.route("/")
def home():
    print("I WORK")
    return "Backend runing!"

# sreya meri jaan call this only for now 


#simple endpoint for testing llm calls
#frontend sends JSON in format: {"prompt": "<prompt_text_here>"}
@app.route("/api/llm-test", methods=["POST"])
def llm_test():
    data = request.get_json() or {}
    prompt = data.get("prompt", "say hello")   #TODO - is say hello really a desirable default?

    try:
        result = call_llm(prompt)

        return jsonify({
            "ok": True,
            "response": result
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500

# Call to get jobs on db
@app.route("/jobs", methods=["GET"])
def list_jobs():
    limit = request.args.get("limit", default=10, type=int)
    limit = max(1, min(limit, 50))

    with get_conn() as conn:
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


if __name__ == "__main__":
    # debug true so for someone reason it no work otherwise 
    app.run(debug=True)
