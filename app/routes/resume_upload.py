import os
from flask import Blueprint, request, jsonify


from app.services.resume_service import process_uploaded_resume

upload_bp = Blueprint("upload", __name__)

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@upload_bp.route("/upload_resume", methods=["POST"])
def upload_resume():
    # Handle resume upload and return resume/extraction ids
    file = request.files.get("resume")

    if not file or not file.filename:
        return jsonify({"ok": False, "error": "No file uploaded under key 'resume'"}), 400

    # filename = secure_filename(file.filename)
    # save_path = os.path.join(UPLOAD_DIR, filename)
    # file.save(save_path)

    try:
        data = process_uploaded_resume(file)
        return jsonify({"ok": True, "file": file.filename, "data": data}), 200
    except Exception as e:
        return jsonify({"ok": False, "file": file.filename, "error": str(e)}), 500
