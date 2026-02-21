from flask import Blueprint

#a simple blueprint for a route to check rest connection health

health_bp = Blueprint("health", __name__)

@health_bp.route("/", methods=["GET"])
def health():
    return {"status": "ok"}