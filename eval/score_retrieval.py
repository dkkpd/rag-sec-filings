import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag.ask import retreive_relevant_chunks

TOP_K = 5
QUESTIONS_PATH = Path(__file__).resolve().parent / "questions.json"



def score_factual(eval_question, chunks):
    tickers = [chunk["ticker"] for chunk in chunks]
    sections = [chunk["section"] for chunk in chunks]
    chunk_text = " ".join(chunk["text"] for chunk in chunks).lower()

    has_expected_ticker = eval_question["expected_ticker"] in tickers
    has_expected_section = any(
        eval_question["expected_section_contains"] in section
        for section in sections
    )
    gold_phrase_found = eval_question["gold"].lower() in chunk_text

    return has_expected_ticker, has_expected_section, gold_phrase_found


def score_compare(eval_question, chunks):
    tickers = [chunk["ticker"] for chunk in chunks] 

    tickers_string = eval_question["expected_ticker"]

    wanted_tickers = []

    for ticker in tickers_string.split(","):
        ticker = ticker.strip()
        if ticker:
            wanted_tickers.append(ticker)

    for ticker in wanted_tickers:
        if ticker not in tickers:
            return False

    return True

def main():
    print("="*60)
    questions = json.load(open(QUESTIONS_PATH, "r", encoding="utf-8"))

    hits = 0
    eligible = 0

    for question in questions:
        if question["type"] == "oos":
            print(f"{question['id']} SKIP (Out-of-scope)")
            continue

        eligible += 1
        chunks = retreive_relevant_chunks(
            question["question"],
            ticker=question["ticker_filter"],
            top_k=TOP_K
        )

        if question["type"] == "compare":
            ok = score_compare(question, chunks)
        else:
            ticker_ok, section_ok, gold_ok = score_factual(question, chunks)
            ok = ticker_ok and section_ok and gold_ok

        shown=[]
        for chunk in chunks:
            shown.append(f"{chunk["ticker"]}:{chunk["section"]}")

        if ok:
            hits += 1
            label = "HIT"
        else:
            label = "MISS"

        if question["type"] == "compare":
            print(f"{question['id']} {label} | tickers={shown}")
        else:
            print(
                f"{question['id']} {label} "
                f"ticker={'Y' if ticker_ok else 'N'} "
                f"section={'Y' if section_ok else 'N'} "
                f"gold={'Y' if gold_ok else 'N'} "
                f"| {shown}"
            )

    print(f"\nretrieval@{TOP_K} = {hits}/{eligible} = {hits/eligible:.2f}")


if __name__ == "__main__":
    main()
            