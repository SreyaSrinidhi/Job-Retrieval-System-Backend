import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename


from app.services.resume_service import extract_skills_from_resume_file

upload_bp = Blueprint("upload", __name__)

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@upload_bp.route("/upload_resume", methods=["POST"])
def upload_resume():
    file = request.files.get("resume")

    if not file or not file.filename:
        return jsonify({"ok": False, "error": "No file uploaded under key 'resume'"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_DIR, filename)
    file.save(save_path)

    try:
        data = extract_skills_from_resume_file(save_path)
        return jsonify({"ok": True, "file_path": save_path, "data": data}), 200
    except Exception as e:
        return jsonify({"ok": False, "file_path": save_path, "error": str(e)}), 500


