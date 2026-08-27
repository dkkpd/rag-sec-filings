FROM python:3.14-slim

WORKDIR /app

COPY docker-requirements.txt .
RUN pip install --no-cache-dir -r docker-requirements.txt
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY main.py .
COPY rag/ rag/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]