"""
Real sentence embeddings for applicant CV profiles -- replaces the random
noise vectors that used to be written to applicant_cvs.cv_embedding.
Used by transform.py's build_applicant_cvs().
"""

from sentence_transformers import SentenceTransformer

_model = None


def get_model():
    global _model
    if _model is None:
        # all-MiniLM-L6-v2 outputs 384-dim vectors -- matches the
        # cv_embedding vector(384) column in schema.sql exactly.
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def embed_text(text: str) -> list[float]:
    model = get_model()
    vec = model.encode(text, normalize_embeddings=True)  # pre-normalized -> cosine similarity == dot product
    return vec.tolist()