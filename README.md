# SEC Filings RAG Assistant

A retrieval-augmented generation (RAG) pipeline that answers questions about the latest 10-K filings for **Walmart (WMT)**, **Capital One (COF)**, and **Alphabet (GOOGL)**.

The system covers **Item 1A (Risk Factors)** and **Item 7 (MD&A)** only. Answers are grounded in retrieved chunks, with citations. If the filings do not support an answer, the model is instructed to say so.

## Run locally

**Clone the repo**
```
git clone https://github.com/dkkpd/rag-sec-filings
cd rag-sec-filings
```

**Create a virtual environment**
```
python -m venv venv
```

**Activate it**
- Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
- macOS / Linux: `source venv/bin/activate`

**Install dependencies**
```
pip install -r requirements.txt
```

**Environment**
- Create a `.env` file in the project root with your Gemini API key. The Google GenAI client reads `GOOGLE_API_KEY`.
- EDGAR identity is set in `ingestion/01_fetch_sections.py` (`set_identity`). Use your own name and email if you re-run fetch.

**Build the vector store (from the repo root)**

Run these in order. Later steps depend on earlier outputs under `data/` and `chroma_db/`.
```
python ingestion/01_fetch_sections.py
python ingestion/02_clean_text.py
python ingestion/03_chunk.py
python ingestion/04_embed.py
```

**Start the API**
```
uvicorn main:app --reload
```

`POST /ask` expects JSON:
```json
{
  "query": "What does Walmart say about e-commerce competition?",
  "ticker": "WMT"
}
```

`ticker` is optional. Use `null` (or omit it) to search all three companies.

## Pipeline

1. **Fetch** — edgartools pulls the latest 10-K HTML for WMT, COF, and GOOGL. Item 1A and Item 7 are extracted by HTML heading.
2. **Clean** — BeautifulSoup strips tags; boilerplate and XBRL-style noise are reduced.
3. **Chunk** — Character windows of **549** with **100** overlap, split **per section** so a chunk does not mix Item 1A and Item 7. Size is chosen so chunks stay near MiniLM’s **256-token** limit.
4. **Embed** — `sentence-transformers/all-MiniLM-L6-v2` embeddings stored in **Chroma** (`chroma_db/`).
5. **Retrieve** — Query embedding, cosine similarity, **top 5** chunks. Optional ticker metadata filter.
6. **Generate** — Gemini (`gemini-3.5-flash-lite`) answers only from retrieved context. Citations are returned as sources. If the model reports that the answer is not in the filings, it is instruced to respond with 'not found in provided filings'

## Retrieval evaluation

I scored retrieval on a labeled set in `eval/questions.json`: **15 factual**, **2 compare**, **2 out-of-scope**. Out-of-scope questions are not used in the retrieval score (the model should refuse them at generation time).

Run from the repo root:
```
python eval/score_retrieval.py
```

**Baseline (k = 5, matching the API)**

| Split | Result |
| --- | --- |
| Factual | 6 / 15 |
| Compare | 1 / 2 |
| **Overall** | **7 / 17 (0.41)** |

A factual hit requires the gold substring in a retrieved chunk, plus the expected ticker and section (`Item 1A` or `Item 7`). A compare hit requires both companies in the top-k.

## What I noticed

- Retrieval often lands on the **right company and section** but **not the gold paragraph**. Raising k from 5 to 6 added one compare hit and did not fix those factual misses, so I kept **k = 5**.
- Compare queries can fill the top-k with **one** company. One of two compare items still fails for that reason.
- Some gold strings appear more than once in a filing (for example a Discover-related sentence in Capital One Item 1A). Substring matching then needs a more unique span.
- Chunking is **character-based**, not paragraph-based. Neighboring text can sit in the previous or next window.

## Generation Evaluation
I ran some hand-labeled questions through the full path, saved their traces to eval/generation_traces.json, then scored the generation with DeepEval `FaithfulnessMetric` (answer vs retreived chunks, Gemini LLM as judge). Out of scope items are checked seperately for refusal.

Run the following from repo root to get the generation evaluation:
```powershell
python eval/dump_generation_traces.py
python eval/score_generation.py
```
*Note that score_generation has a timer delay of 15 secs per call to avoid hitting the free Gemini API limits. Feel free to delete or modify based on your API limits*

**Results**
| Check | Result |
| --- | --- |
| Mean faithfulness (17 in-scope) | **0.97** |
| Out-of-scope refuse | **2 / 2** |

*Faithfulness measures whether the answer stays grounded in the **retrieved** chunks. The answer can be faithfulness and still incorrect if retrieval fails. Faithfulness should not be confused for accuracy*

For every in-scope answer that said `not found in provided filings`, the gold span (or both companies, for compare) was **missing** from the top-5 contexts. There was **no** case where retrieval had the gold text and the model still refused. Those refuses line up with retrieval misses (and expected OOS behavior), not with the generator ignoring good context.
Compare queries still often retrieve only one company; the model then answers that side and refuses the other. 

The questions in `questions.json` are hand-picked with the answers actually in the filings. Therefore, all the questions besides from the out of scope ones should all have answers; none of them should result in a 'not found in provided filings'. However, we still have some of the questions resulting in exactly that result, which indicates a bottleneck in retreival, not in generation. After all, the gemini model only knows what retreival feeds it.


## Limitations

- Three issuers, two 10-K items, latest filing only. Not much data, just a starting point.
- MiniLM is a small encoder; dense retrieval misses when the question wording is far from the filing.
- No hybrid search, reranker, or query rewriting.
- Chunking is based on just character limits, data such as financial tables and so can get lost when chunking.
- Gemini can still hallucinate and make up answers even from the provided sources. It's still up to the Gemini model to produce "not found" phrasing.
- HTML heading-based section extract can miss or over-include content on messy 10-Ks.
- API only. No frontend or deployments **yet**.
