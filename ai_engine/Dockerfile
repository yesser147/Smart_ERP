FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/hf \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# libgomp1: OpenMP runtime needed by XGBoost
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only PyTorch (the default one ships ~2 GB of GPU libraries we don't use)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# download the embedding model at build time: no internet needed at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

RUN useradd --system --uid 1001 ai && chown -R ai /app /opt/hf
USER ai

EXPOSE 8000
# secrets come from ai_engine/.env through docker-compose (never baked into the image)
CMD ["python", "main_api.py"]
