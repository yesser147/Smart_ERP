"""
Single-applicant CV processing, triggered by the "Traiter CV" button.
Pipeline: download PDF from MinIO -> extract raw text (pdfplumber) ->
hand off to cv_intelligence_core for LLM structuring + embedding.

The button always runs the FULL pipeline through skills extraction --
there's no "extract text only" path. If parsed_text already exists
(e.g. re-processing), the PDF download/extraction step is skipped, but
structure_and_embed() always runs.
"""

import io
import requests
import pdfplumber
from sqlalchemy import text
from database import engine
from models.recruitment.cv_intelligence_core import structure_and_embed, write_results


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """pdfplumber does the actual PDF-to-text extraction -- Ollama never
    sees the PDF binary, only the resulting plain text."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def download_pdf(file_url: str) -> bytes:
    response = requests.get(file_url, timeout=30)
    response.raise_for_status()
    return response.content


def process_applicant_cv(applicant_id: int) -> dict:
    """Full pipeline for one applicant: (extract text if not already
    done) -> LLM structuring -> embedding -> write everything back.
    Returns a status dict the endpoint hands straight to the frontend."""
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT ac.file_url, ac.parsed_text
            FROM applicant_cvs ac
            WHERE ac.applicant_id = :aid
        """), {"aid": applicant_id}).fetchone()

    if row is None:
        return {"status": "error", "message": "Aucun CV trouvé pour ce candidat."}

    resume_text = row.parsed_text
    if not resume_text:
        if not row.file_url:
            return {"status": "error", "message": "Aucun fichier CV n'a été téléversé."}
        try:
            pdf_bytes = download_pdf(row.file_url)
            resume_text = extract_text_from_pdf_bytes(pdf_bytes)
        except Exception as e:
            return {"status": "error", "message": f"Échec de l'extraction du PDF: {e}"}

        if not resume_text:
            return {"status": "error", "message": "Le PDF ne contient aucun texte extractible (scan image ?)."}

        with engine.begin() as conn:
            conn.execute(text("UPDATE applicant_cvs SET parsed_text = :txt WHERE applicant_id = :aid"),
                         {"txt": resume_text, "aid": applicant_id})

    # This is the step that was at risk of being skipped -- now it's the
    # only path through structure_and_embed, guaranteed to run every time.
    try:
        result = structure_and_embed(resume_text)
    except Exception as e:
        return {"status": "error", "message": f"Échec de l'analyse LLM: {e}"}

    with engine.begin() as conn:
        write_results(conn, applicant_id, result)

    return {
        "status": "success",
        "skills": result["skills"],
        "years_of_experience": result["years_of_experience"],
        "education_level": result["education_level"],
        "summary": result["summary"],
    }