import json
import chromadb
from sentence_transformers import SentenceTransformer

with open("data/chunks/all_chunks.json", 'r', encoding='utf-8') as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} chunks")

model = SentenceTransformer("all-MiniLM-L6-v2")
print("max_seq_length:", model.max_seq_length)

