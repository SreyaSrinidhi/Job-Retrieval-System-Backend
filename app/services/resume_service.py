import re
import time
from typing import Any, Dict, List
from werkzeug.datastructures import FileStorage
from app.services.embedding_service import embed_text
from app.services.database_service import compute_matches_for_resume

from app.services.resume_utils.resume_parser import (
    parse_resume_file,
    looks_like_scanned_or_empty,
)
from app.services.prompt_loader import load_prompt_text
from app.services.llm_service import call_llm_json
from app.services.database_service import (
    clear_matches_for_resume,
    create_or_update_matches,
    create_resume,
    create_resume_extraction,
    get_latest_resume_extraction,
    list_active_jobs_for_matching,
    list_top_matches_for_resume,
)


#JSON schema for extracted skills from resume 
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

#helper method to extract skills from text of a resume
#takes in user_job_description to instruct LLM on what keywords to value
def extract_skills_from_resume_text(resume_text: str, user_intent: str) -> Dict[str, Any]:
    # Run validation + LLM keyword extraction on already parsed resume text
    if looks_like_scanned_or_empty(resume_text):
        raise ValueError(
            "Resume text extraction looks empty (possibly a scanned PDF). "
            "Try uploading a text-based PDF or DOCX."
        )

    template = load_prompt_text("extract_relevant_skills.txt") if user_intent else load_prompt_text("extract_all_skills.txt") 
    template = template.replace("{{USER_INTENT}}", user_intent or "")   #Add user intent - will do nothing for prompt where this field does not exist
    prompt = template.replace("{{RESUME_TEXT}}", resume_text)

    return call_llm_json(prompt, _SKILLS_SCHEMA)

# Full upload flow: parse resume, extract keywords, and store both records in db
def process_uploaded_resume(file: FileStorage, user_job_description: str) -> Dict[str, Any]:
    resume_text = parse_resume_file(file)
    extracted_skills = extract_skills_from_resume_text(resume_text, user_job_description)

    resume_embedding = generate_resume_embedding(extracted_skills)

    resume_id = create_resume(resume_text=resume_text, filename=file.filename)
    extraction_id = create_resume_extraction(
        resume_id=resume_id,
        extracted_json=extracted_skills,
        embedding=resume_embedding,
        model_name="gemini-2.5-flash",
    )

    return {
        "resume_id": resume_id,
        "extraction_id": extraction_id,
        "extracted": extracted_skills,
    }


def _normalize_keywords(extracted_json: Dict[str, Any]) -> List[str]:
    # Normalize and deduplicate extracted keywords for matching
    candidates: List[str] = []

    for key in ("skills", "keywords", "key_words"):
        value = extracted_json.get(key)
        if isinstance(value, list):
            candidates.extend(str(v) for v in value)

    seen = set()
    normalized: List[str] = []
    for item in candidates:
        cleaned = re.sub(r"\s+", " ", item.strip().lower())
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized


def _tokenize_text(text: str) -> set[str]:
    # Tokenize job text into searchable lowercase terms
    return set(re.findall(r"[a-z0-9+#.\-]+", text.lower()))

def score_resume_against_jobs(resume_id: int) -> Dict[str, Any]:
    # 1. Get latest extraction (contains embedding)
    extraction = get_latest_resume_extraction(resume_id)
    if not extraction:
        raise ValueError(f"No extraction found for resume_id={resume_id}")

    resume_embedding = extraction.get("embedding")
    if resume_embedding is None:
        raise ValueError("Resume embedding not found")

    # 2. Clear old matches
    clear_matches_for_resume(resume_id)

    # 3. Compute matches using DB (THIS is the key)
    rows = compute_matches_for_resume(resume_id, resume_embedding, top_k=50)
    print ("[DEBUG] Row length", len(rows))

    # 4. Build payload
    matches = []
    for job_id, similarity in rows:
        matches.append([
            resume_id,
            int(job_id),
            float(similarity),
            None,
            {}
        ])

    # 5. Store matches
    create_or_update_matches(matches)

    return {
        "resume_id": resume_id,
        "matches_saved": len(matches),
    }


def get_display_jobs_for_resume(resume_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    # Fetch top ranked jobs to send to the frontend
    return list_top_matches_for_resume(resume_id=resume_id, limit=limit)


def build_resume_embedding_text_from_keywords(keywords: List[str]) -> str:
    return "Skills: " + ", ".join(keywords)

def generate_resume_embedding(extracted_json: Dict[str, Any]) -> List[float]:
    keywords = _normalize_keywords(extracted_json)
    text = build_resume_embedding_text_from_keywords(keywords)
    return embed_text(text)