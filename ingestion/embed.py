import json
import chromadb
from sentence_transformers import SentenceTransformer

with open("data/chunks/all_chunks.json", 'r', encoding='utf-8') as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} chunks")

model = SentenceTransformer("all-MiniLM-L6-v2")
print("max_seq_length:", model.max_seq_length)

token_lengths = []
oversized_chunks = 0
oversized = []

for chunk in chunks:
    length = len(model.tokenizer.encode(chunk["text"]))
    if length > model.max_seq_length:
        oversized_chunks += 1
        oversized.append(length)
    token_lengths.append(length)

print("First 20 token lengths:", token_lengths[:20])
print("Max token length:", max(token_lengths))
print("Oversized chunks:", oversized_chunks)
print("Oversized token lengths:", oversized)

texts = [chunk["text"] for chunk in chunks]
embeddings = model.encode(texts, show_progress_bar=True)

client = chromadb.PersistentClient(path = "chroma_db")

try:
    client.delete_collection("sec_filings")
except Exception as e:
    pass

collection = client.get_or_create_collection(name="sec_filings")
collection.add(
    ids=[chunk["id"] for chunk in chunks],
    documents=[chunk["text"] for chunk in chunks],
    embeddings=embeddings.tolist(),
    metadatas=[
        {
            "company": chunk["company"],
            "ticker": chunk["ticker"],
            "section": chunk["section"],
            "chunk_index": chunk["chunk_index"]
        }
        for chunk in chunks
    ]
)

print(f"Stored {collection.count()} vectors in ChromaDB collection 'sec_filings'")

#--------------- Test querying the collection ---------------
queries = [
    "What risks does Walmart face in its retail operations?",
    "How does Capital One describe credit card or credit risk?",
    "How does Alphabet describe advertising, search, or regulatory risk?",
]

for query in queries:
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=3,
        include=["documents", "metadatas", "distances"]
    )

    print("\n" + "=" * 60)
    print("Q:", query)
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        print(f"\n  {meta['ticker']} | {meta['section']} | distance={dist:.3f}")
        print(f"  {doc[:200]}...")  # Print first 500 characters of the document

