const API_URL = "http://127.0.0.1:8000/ask";

const questionEl = document.getElementById("question");
const companyEl = document.getElementById("company");
const askBtn = document.getElementById("ask-btn");
const answerBox = document.getElementById("answer-box");
const sourcesList = document.getElementById("sources-list");

function setLoading(loading) {
  askBtn.disabled = loading;
  askBtn.textContent = loading ? "Asking…" : "Ask";
}

function showAnswer(text, isError) {
  answerBox.innerHTML = "";
  const p = document.createElement("p");
  p.textContent = text;
  if (isError) {
    p.className = "error";
  }
  answerBox.appendChild(p);
}

function showSources(sources) {
  sourcesList.innerHTML = "";

  if (!sources || sources.length === 0) {
    const li = document.createElement("li");
    li.className = "source-item placeholder-item";
    li.innerHTML =
      '<span class="source-company">—</span>' +
      '<span class="source-section">No sources returned.</span>';
    sourcesList.appendChild(li);
    return;
  }

  for (const source of sources) {
    const li = document.createElement("li");
    li.className = "source-item";
    li.innerHTML =
      `<span class="source-company">${source.company} (${source.ticker})</span>` +
      `<span class="source-section">${source.section}</span>`;
    sourcesList.appendChild(li);
  }
}

async function ask() {
  const query = questionEl.value.trim();
  if (!query) {
    showAnswer("Enter a question first.", true);
    return;
  }

  const ticker = companyEl.value || null;

  setLoading(true);
  showAnswer("Loading…", false);
  showSources([]);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, ticker }),
    });

    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`);
    }

    const data = await response.json();
    showAnswer(data.answer || "No answer returned.");
    showSources(data.sources);
  } catch (err) {
    showAnswer(
      "Could not reach the API. Start the server with: uvicorn main:app --reload",
      true
    );
  } finally {
    setLoading(false);
  }
}

askBtn.addEventListener("click", ask);

questionEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    ask();
  }
});
