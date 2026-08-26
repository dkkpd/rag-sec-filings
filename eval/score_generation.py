import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv


from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase
from deepeval.models import GeminiModel

load_dotenv()

TRACES_PATH = Path(__file__).resolve().parent / "generation_traces.json"
REFUSE_PHRASE = "not found in provided filings"

def oos_ok(trace):
    refused = REFUSE_PHRASE in trace["answer"].lower()
    return refused

def sources_ok(trace):
    return len(trace["sources"]) > 0


def main():

    traces = json.load(open(TRACES_PATH, "r", encoding="utf-8"))


    judge = GeminiModel(
        model="gemini-3.5-flash-lite",
        api_key = os.environ.get("GEMINI_API_KEY")
    )

    faithfulness_metric = FaithfulnessMetric(
        model = judge,
        include_reason = False, # save gemini calls
        async_mode = False
    )

    faithfulness_scores = []

    for trace in traces:
        question_id = trace["id"]
        question_type = trace["type"]

        if question_type == "oos":
            ok = oos_ok(trace)
            print(f"{question_id} OOS {'PASS' if ok else 'FAIL'}")
            continue

        test_case = LLMTestCase(
            input = trace["question"],
            actual_output = trace["answer"],
            retrieval_context = trace["contexts"]
        )
        faithfulness_metric.measure(test_case)
        time.sleep(15) # wait 15 seconds between calls to avoid rate limiting issues with gemini api

        src = sources_ok(trace)
        faithfulness_scores.append(faithfulness_metric.score)

        print(
        f"{question_id} faith={faithfulness_metric.score:.2f} "
        f"sources={'Y' if src else 'N'} "
        f"| {faithfulness_metric.reason}"
        )

    if faithfulness_scores:
        mean = sum(faithfulness_scores) / len(faithfulness_scores)
        print(f"\nmean faithfulness = {mean:.2f} over {len(faithfulness_scores)} in-scope questions")

if __name__ == "__main__":
    main()



