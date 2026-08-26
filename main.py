from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from rag.ask import ask as run_ask
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded



limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RateLimitExceeded)
def rate_limit_exceeded_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"message": "Rate limit exceeded. Please try again later."},
    )

class AskRequest(BaseModel):
    query: str
    ticker: str | None = None

@app.post("/ask")
@limiter.limit("10/minute")
def ask_endpoint(request: Request,ask_request: AskRequest):
    query = ask_request.query
    ticker = ask_request.ticker

    result = run_ask(query, ticker)
    return(result)

@app.get("/")
def root():
    return {"message": "Welcome to the SEC Filings RAG API. Use the /ask endpoint to ask questions."}