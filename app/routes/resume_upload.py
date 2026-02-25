import os
from flask import Blueprint, request
from werkzeug.utils import secure_filename

upload_bp = Blueprint("upload", __name__)

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@upload_bp.route("/upload_resume", methods=["POST"])
def upload_resume():
    file = request.files.get("resume")

    if not file or not file.filename:
        return "", 400  # bad request

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_DIR, filename)

    file.save(save_path)

    return "", 200  # success