# C:\Users\yasser\Documents\stage\Smart_ERP_Core\ai_engine\embeddings.py
"""
Real sentence embeddings for candidate/job matching. Same model as the
ETL's embeddings.py (kept in sync manually since this is a separate
Python project) -- 384-dim output matches applicant_cvs.cv_embedding.
"""

from sentence_transformers import SentenceTransformer

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def embed_text(text: str) -> list[float]:
    model = get_model()
    vec = model.encode(text, normalize_embeddings=True)  # pre-normalized -> cosine similarity == dot product
    return vec.tolist()