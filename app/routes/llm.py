from flask import Blueprint, jsonify, request
from app.services import llm_service

llm_bp = Blueprint("gemini", __name__)

#simple endpoint for testing llm calls
#frontend sends JSON in format: {"prompt": "<prompt_text_here>"}
@llm_bp.route("/llm_test", methods=["POST"])
def llm_test():
    data = request.get_json() or {}
    prompt = data.get("prompt", "say hello")   #NOTE - is say hello really a desirable default?

    try:
        result = llm_service.call_llm(prompt)

        return jsonify({
            "ok": True,
            "response": result
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500