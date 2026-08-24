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

    chunks = []

    for doc, metadata, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        chunks.append({
            "text": doc,
            "company": metadata["company"],
            "ticker": metadata["ticker"],
            "section": metadata["section"],
            "distance": dist
        })
    return chunks

def build_prompts(query, chunks):
    parts = []

    for i, chunk in enumerate(chunks):
        parts.append(
            f"[Source {i+1}] | {chunk['company']} ({chunk['ticker']}) | {chunk['section']}\n"
            f"{chunk['text']}"
        )

    context = "\n\n".join(parts)

    prompt = f"""You are answering questions about SEC 10-K filings. 

    Use ONLY the context below. Pull information ONLY from the context below. If the answer is not in the context, say "not found in provided filings".
    When you do answer, cite the company and section of the filing you are referencing in your answer. For example, if you are referencing a section from Walmart's 10-K filing, you would say "According to Walmart's 10-K filing, [section name]...".

    Context:
    {context}

    Question: {query}

    Answer:"""

    return(prompt)

def ask(question, ticker=None):
    chunks = retreive_relevant_chunks(question, ticker=ticker)
    prompt = build_prompts(question, chunks)

    interaction = gemini.interactions.create(
        model= "gemini-3.5-flash-lite",
        input = prompt
    )

    sources = []
    seen = set()

    # --------- Collect unique sources from the chunks ---------
    for chunk in chunks:
        key = (chunk["ticker"], chunk["section"])
        if key not in seen:
            seen.add(key)
            sources.append({
                "ticker": chunk["ticker"],
                "company": chunk["company"],
                "section": chunk["section"]
            })
    # ----------------------------------------------------------

    if "not found in provided filings" in interaction.output_text.lower():
        sources = [] # if the answer is not found in the filings, return an empty list of sources

    return {
        "question": question,
        "answer": interaction.output_text,
        "sources": sources
    }

if __name__ == "__main__":
    tests = [
        ("What risks does Walmart face in its retail operations?", "WMT"),
        ("How does Capital One describe credit card or credit risk?", "COF"),
        ("How does Alphabet describe advertising, search, or regulatory risk?", "GOOGL"),
        ("What are the key risks between Walmart and Capital One?", None),
        ("What risks does Tesla face?", None) # test if model is able to say "not found in provided filings" when the answer is not in the context
    ]

    for question, ticker in tests:
        print("\n" + "="*80)
        result = ask(question, ticker=ticker)
        print(f"Question: {result['question']} | ticker filter: {ticker}")
        print(f"Answer: {result['answer']}")
        print(f"\nSources:")
        if not result['sources']:
            print("- No sources found in provided filings.")
        for source in result['sources']:
            print(f"- {source['company']} ({source['ticker']}) | {source['section']}")


