FROM python:3.11-slim

# Tesseract must be baked into the image per DEMO.md's pre-demo-machine
# checklist ("confirm it's in the Docker image, not just installed on
# the original dev machine").
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model at BUILD time, not first request. This
# needs network access during `docker-compose build` (once), but means a
# flaky/restricted network at runtime can never stall an upload or a Q&A
# query waiting on a ~2GB Hugging Face download.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
