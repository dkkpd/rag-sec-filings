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
    parts = []

    for i, hit in enumerate(hits):
        parts.append(
            f"[Source {i+1}] | {hit['company']} ({hit['ticker']}) | {hit['section']}\n"
            f"{hit['text']}"
        )

    context = "\n\n".join(parts)

    prompt = f"""You are answering questions about SEC 10-K filings. 

    Use ONLY the context below. Pull information ONLY fron the context below. If the answer is not in the context, say "not found in provided filings".
    When you do answer, cite the company and section of the filing you are referencing in your answer. For example, if you are referencing a section from Walmart's 10-K filing, you would say "According to Walmart's 10-K filing, [section name]...".

    Context:
    {context}

    Question: {query}

    Answer:"""

    print(prompt)

    return(prompt)

build_prompts("What risks does capital one face in its consumer lending operations?", retreive_relevant_chunks("What risks does capital one face in its consumer lending operations?", ticker="COF"))


    

