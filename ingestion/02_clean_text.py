import json
import re
import os

def clean_text(text):
    text = text.replace("\u00a0", " ") # replace non-breaking spaces with regular spaces
    text = re.sub(r"\n\s*\d{1,4}\s*\n", "\n\n", text) # replace page numbers with newlines
    text = re.sub(r"\n{3,}", "\n\n", text) # replace multiple newlines with two newlines
    text = re.sub(r"[ \t]+", " ", text) # replace multiple spaces/tabs with a single space
    return text.strip() # remove leading/trailing whitespace

os.makedirs("data/cleaned", exist_ok=True) # make a data folder if it doesn't exist

for filename in os.listdir("data/raw"):
    if not filename.endswith(".json"):
        continue # skip non-JSON files

    with open(f"data/raw/{filename}", 'r', encoding='utf-8') as f:
        records = json.load(f)

    for record in records:
        original_len = len(record["text"])
        record["text"] = clean_text(record["text"])
        cleaned_len = len(record["text"])
        print(f"{record['ticker']} - {record['section']}: {original_len} -> {cleaned_len} characters")

    out_path = f"data/cleaned/{filename}"

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
    