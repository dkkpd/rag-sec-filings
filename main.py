from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag.ask import ask as run_ask

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    query: str
    ticker: str | None = None

@app.post("/ask")
def ask_endpoint(ask_request: AskRequest):
    query = ask_request.query
    ticker = ask_request.ticker

    result = run_ask(query, ticker)
    return(result)

@app.get("/")
def root():
    return {"message": "Welcome to the SEC Filings RAG API. Use the /ask endpoint to ask questions."}