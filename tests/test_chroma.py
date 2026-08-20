import chromadb

client = chromadb.Client()
collection = client.create_collection(name="test")

collection.add(
    documents=["Walmart is a retail company.", "Capital One is a bank."],
    ids=["doc1", "doc2"]
)

results = collection.query(query_texts=["Tell me about finance"], n_results=1)
print(results["documents"])