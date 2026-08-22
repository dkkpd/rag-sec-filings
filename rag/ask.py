import os
from google import genai
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb

load_dotenv()

TOP_K = 5 # number of top results to return

# --------- Load the model, ChromaDB client, and Gemini client ---------
model = SentenceTransformer("all-MiniLM-L6-v2")
chroma = chromadb.PersistentClient(path = "chroma_db")
collection = chroma.get_collection("sec_filings")
gemini = genai.Client()
# ----------------------------------------------------------------------

def retreive_relevant_chunks(query, ticker=None, top_k=TOP_K):
    query_embedding = model.encode([query]).tolist()

    kwargs = {
        "query_embeddings": query_embedding,
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"]
    }

    if ticker:
        kwargs["where"] = {"ticker": ticker} # add a filter for the ticker if the ticker is provided

    results = collection.query(**kwargs)

    hits = []

    for doc, metadata, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        hits.append({
            "text": doc,
            "company": metadata["company"],
            "ticker": metadata["ticker"],
            "section": metadata["section"],
            "distance": dist
        })
    return hits

def build_prompts(query, hits):
    prompt = f"Answer the following question based on the provided context:\n\nQuestion: {query}\n\nContext:\n"

    for i, hit in enumerate(hits):
        prompt += (
            f"Source 1 {i+1} (Company: {hit['company']}, Ticker: {hit['ticker']}, "
            f"Section: {hit['section']}):\n "
            f"{hit['text']}\n\n"
        )

    print(" Prompt built:\n", prompt)
    

    prompt += "Please provide a concise and accurate answer based on the above context."
    return prompt

build_prompts("What risks does Walmart face in its retail operations?", retreive_relevant_chunks("What risks does Walmart face in its retail operations?", ticker="WMT"))


    

