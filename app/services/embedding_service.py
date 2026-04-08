from dotenv import load_dotenv
import os
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer

load_dotenv()

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str) -> List[float]:
    return model.encode(text).tolist()


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    v1 = np.array(vec1)
    v2 = np.array(vec2)

    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


def compare_texts(text1: str, text2: str) -> float:
    emb1 = embed_text(text1)
    emb2 = embed_text(text2)

    return cosine_similarity(emb1, emb2)