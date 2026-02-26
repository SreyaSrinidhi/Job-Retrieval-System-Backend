import os
from typing import Any, Dict
from werkzeug.datastructures import FileStorage

from app.services.resume_utils.resume_parser import (
    parse_resume_file,
    looks_like_scanned_or_empty,
)
from app.services.prompt_loader import load_prompt_text
from app.services.llm_service import call_llm_json


#simple one we can change it later 
_SKILLS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "skills": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    },
    "required": ["skills"]
}


def extract_skills_from_resume_file(file: FileStorage) -> Dict[str, Any]:
    # if not os.path.exists(file):
        # raise FileNotFoundError(f"Resume file not found: {file}")

    # _, ext = os.path.splitext(file)
    # ext = ext.lower().lstrip(".")
    # if ext not in {"pdf", "docx"}:
        # raise ValueError("Unsupported file type (only pdf, docx)")

    resume_text = parse_resume_file(file)

    if looks_like_scanned_or_empty(resume_text):
        raise ValueError(
            "Resume text extraction looks empty (possibly a scanned PDF). "
            "Try uploading a text-based PDF or DOCX."
        )

    template = load_prompt_text("extract_skills.txt")
    prompt = template.replace("{{RESUME_TEXT}}", resume_text)

    result = call_llm_json(prompt, _SKILLS_SCHEMA)
    print (result)

    return result