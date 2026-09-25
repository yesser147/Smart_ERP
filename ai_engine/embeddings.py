"""
Sentence embeddings for CVs, jobs and skills (384 dimensions, matching the
applicant_cvs.cv_embedding vector(384) column).

EMBEDDING_MODEL (.env) selects the model. Any 384-dimension model works, e.g.
  all-MiniLM-L6-v2                        (default, English)
  paraphrase-multilingual-MiniLM-L12-v2   (French, Arabic, ... CVs)
After changing it, re-embed the stored CVs:
  python -m models.recruitment.reindex_embeddings
"""

import os

from sentence_transformers import SentenceTransformer

MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_text(text: str) -> list[float]:
    return get_model().encode(text, normalize_embeddings=True).tolist()
