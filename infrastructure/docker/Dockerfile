# FieldCore API + ingestion worker
# Run API: docker run -p 8000:8000 -e DATABASE_URL=... -e OPENAI_API_KEY=... fieldcore-api
# Run worker: docker run --entrypoint python -e DATABASE_URL=... -e OPENAI_API_KEY=... fieldcore-api -m src.workers.ingestion_worker

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/

# Default: run FastAPI
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
