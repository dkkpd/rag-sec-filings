import json
import os

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

def slug(section):
    return (
        section.replace(" ", "_")
        .replace(":", "")
        .replace("'", "")
        .replace('"', "")
    )

def chunk_text(text, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be less than chunk_size")

    chunks=[]
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])

        if end == len(text):
            break

        start = end - chunk_overlap

    return chunks

os.makedirs("data/chunks", exist_ok=True) # make a data folder if it doesn't exist

all_chunks = []

for filename in os.listdir("data/cleaned"):
    if not filename.endswith(".json"):
        continue # skip non-JSON files

    with open(f"data/cleaned/{filename}", 'r', encoding='utf-8') as f:
        records = json.load(f)

    for record in records:
        pieces = chunk_text(record["text"])
        lengths = [len(piece) for piece in pieces]

        print(
            f'{record["ticker"]} - {record["section"]}: '
            f'{len(record["text"])} characters -> '
            f'{len(pieces)} chunks | '
            f'min={min(lengths)} avg= {sum(lengths)/len(lengths):.2f} max={max(lengths)}'
        )

    for i, piece in enumerate(pieces):
        all_chunks.append({
            "id": f"{record['ticker']}_{slug(record['section'])}_{i}",
            "text": piece,
            "company": record["company"],
            "ticker": record["ticker"],
            "section": record["section"],
            "chunk_index": i
        })

out_path = "data/chunks/all_chunks.json"
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(all_chunks, f, indent=2)

print(f"\nTotal chunks: {len(all_chunks)}")
print(f"Saved to {out_path}")
