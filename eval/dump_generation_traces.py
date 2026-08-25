import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag.ask import ask

QUESTIONS_PATH = Path(__file__).resolve().parent / "questions.json"
OUT_PATH = Path(__file__).resolve().parent / "generation_traces.json"

questions = json.load(open(QUESTIONS_PATH, "r", encoding="utf-8"))

traces = []

# loop through questions.json, call ask(), store results in traces as list of dicts, and write to generation_traces.json
for question in questions:
    result = ask(question["question"], ticker=question["ticker_filter"])

    traces.append({
        "id": question["id"],
        "type" : question["type"],
        "question": question["question"],
        "ticker_filter": question["ticker_filter"],
        "answer": result["answer"],
        "sources": result["sources"],
        "contexts": result["context"]
    })
    print(question["id"], "ok", len(result["context"]), "chunks")

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(traces, f, indent=4, ensure_ascii=False)


print("wrote", OUT_PATH, "n=", len(traces))
