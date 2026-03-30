import re
import time
from typing import Any, Dict, List
from werkzeug.datastructures import FileStorage

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

    resume_id = create_resume(resume_text=resume_text, filename=file.filename)
    extraction_id = create_resume_extraction(
        resume_id=resume_id,
        extracted_json=extracted_skills,
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
    # Score one resume against all active jobs and persist match rows
    # TODO - we need to add more complex scoring logic later

    extraction = get_latest_resume_extraction(resume_id)
    if not extraction:
        raise ValueError(f"No extraction found for resume_id={resume_id}")

    extracted_json = extraction.get("extracted_json")
    if not isinstance(extracted_json, dict):
        raise ValueError(f"Invalid extraction payload for resume_id={resume_id}")

    keywords = _normalize_keywords(extracted_json)

    clear_matches_for_resume(resume_id)

    if not keywords:
        return {"resume_id": resume_id, "keywords": 0, "jobs_scored": 0, "matches_saved": 0}

    jobs = list_active_jobs_for_matching()
    matches_saved = 0
    matches = []
    
    for job in jobs:
        tags = job.get("tags") or []
        if isinstance(tags, list):
            tags_text = " ".join(str(tag) for tag in tags)
        else:
            tags_text = str(tags)

        combined_text = " ".join(
            [
                str(job.get("title") or ""),
                str(job.get("company") or ""),
                str(job.get("location") or ""),
                str(job.get("description") or ""),
                tags_text,
            ]
        ).lower()

        tokens = _tokenize_text(combined_text)

        matched_keywords: List[str] = []

        for keyword in keywords:
            if " " in keyword:
                if keyword in combined_text:
                    matched_keywords.append(keyword)
            elif keyword in tokens:
                matched_keywords.append(keyword)

        if not matched_keywords:
            continue

        score = round((len(matched_keywords) / len(keywords)) * 100.0, 2)
        explanation = f"Matched {len(matched_keywords)} of {len(keywords)} keywords."
        metadata = {"matched_keywords": matched_keywords, "total_keywords": len(keywords)}

        #add to list of matches
        matches.append([resume_id, int(job["id"]), score, explanation, metadata])
        matches_saved += 1

    #update matches in DB
    create_or_update_matches(matches)

    return {
        "resume_id": resume_id,
        "keywords": len(keywords),
        "jobs_scored": len(jobs),
        "matches_saved": matches_saved,
    }


def get_display_jobs_for_resume(resume_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    # Fetch top ranked jobs to send to the frontend
    return list_top_matches_for_resume(resume_id=resume_id, limit=limit)
