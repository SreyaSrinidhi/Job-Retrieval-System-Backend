from flask import Blueprint, jsonify, request
from app.services import file_processing_service
#NOTE - ethan's old - to be deleted


files_bp = Blueprint("files", __name__)

#endpoint for uploading resume file
#frontend sends JSON in format: {"prompt": "<prompt_text_here>"}
@files_bp.route("/upload_resume", methods=["POST"])
def upload_resume():
    #ensure file in request
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files["file"]

    #ensure that file is valid
    if file.filename == "":
        return jsonify({"error": "No File Selected"}), 400
    
    #pass file to services layer for processing
    try:
        result = file_processing_service.process_resume(file)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify({"ok": True, "response": result})