from dotenv import load_dotenv
import os
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer

load_dotenv()

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str) -> List[float]:
    return model.encode(text).tolist()


# def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
#     v1 = np.array(vec1)
#     v2 = np.array(vec2)

#     return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


# def compare_text_to_job(emb1, emb2, job_id) -> float:
#     if emb2 is None:
#         raise ValueError(f"No embedding found for job_id={job_id}")

#     return cosine_similarity(emb1, emb2)

def build_job_embedding_text(job):
    tags = job.get("tags") or []

    if isinstance(tags, list):
        tags_str = ", ".join(tags)
    else:
        tags_str = str(tags)

    return f"""
    Job Posting:

    Title: {job["title"]}
    Company: {job["company"]}

    Required Skills: {tags_str}
    Key Skills: {tags_str}

    Description: {job.get("description", "")}

    This role is for a {job["title"]} requiring skills in {tags_str}.
    """