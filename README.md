# 🛍️ Retail Insights

**Ask your retail data questions in plain English. Get real SQL-backed answers, instantly.**

Retail Insights is a natural-language analytics dashboard built on **Exasol**, powered by an **LLM-driven NL-to-SQL engine**. Instead of writing SQL or digging through spreadsheets, ask questions like *"which product has the highest profit margin?"* or *"which country has the highest number of orders?"* and get a real, data-backed answer — generated live against your actual database.

Built by **Team SAKS** for the **Exasol AI Build Challenge 2026**.

---

### 🎥 Demo Video

[**Watch the demo here**](https://www.youtube.com/watch?v=I0uawXPWKeE)

---

## ✨ Why Retail Insights?

Retail teams sit on huge amounts of transactional data but most people who need answers from it — merchandisers, category managers, ops leads — can't write SQL. Retail Insights closes that gap:

- **No SQL required** — ask questions in plain English, get accurate answers.
- **Built on Exasol** — a high-performance analytics database, so queries run fast even at scale (200K+ rows and growing).
- **Real business metrics out of the box** — revenue, growth, profit margin, restock risk, product benchmarking — not just a chatbot wrapper.
- **Handles both data questions and theory questions** — ask "which product has the highest margin?" or "what's the difference between gross and net margin?" and get a correct answer either way.
- **Safe by design** — every LLM-generated query is validated before it touches the database (table allowlist, no destructive statements).
- **Actually explainable** — answers are grounded in real query results, not hallucinated summaries, with an option to view the exact SQL that was run.

---

## 🚀 Features

| Feature | What it does |
|---|---|
| 📊 **KPI Dashboard** | Revenue, order volume, and month-over-month growth at a glance |
| 📈 **Sales Trend** | Visualizes sales over time to spot seasonality and momentum |
| 🏆 **Top Products** | Ranks best-selling products by revenue and volume |
| 💰 **Profit & Margin Analysis** | Surfaces which products and categories are actually profitable, not just high-revenue |
| ⚠️ **Restock Alerts** | Flags products trending toward stockouts based on recent sales velocity |
| 🌍 **Country Benchmarking** | Compares performance across markets/countries |
| ⚡ **Query Speed Demo** | One-click benchmark showing Exasol scanning 200,000+ rows in ~2 seconds |
| 💬 **Ask Anything (NL-to-SQL)** | Type a question in plain English → LLM generates SQL → runs on Exasol → returns a natural-language answer. Also answers general retail-theory questions (e.g. "what is basket analysis?") without needing the database. |

---

## 🧠 How It Works

1. You type a question into the dashboard (e.g. *"which product has the highest profit margin?"*).
2. The backend sends your question, plus the database schema, to an LLM (via Groq) with strict instructions to produce **valid Exasol SQL only** — or, for conceptual/theory questions, to answer directly from its own knowledge.
3. If SQL is generated, it's validated first — checked against an allowlist of tables and blocked from any destructive operations — before it's run.
4. The query executes directly against **Exasol**, and the result is turned back into a plain-English answer.
5. The dashboard renders it instantly, alongside the underlying data and (optionally) the exact SQL that was run.

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Database** | [Exasol](https://www.exasol.com/) (SaaS trial) — high-performance in-memory analytics database |
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Python) |
| **Backend Language / Runtime** | Python 3.12 |
| **Database Driver** | [pyexasol](https://github.com/exasol/pyexasol) |
| **LLM Provider** | [Groq](https://groq.com/) — running `openai/gpt-oss-120b` |
| **LLM Client** | Groq Python SDK |
| **Frontend** | HTML5, CSS3, vanilla JavaScript (no framework, no build step) |
| **Charting** | [Chart.js](https://www.chartjs.org/) (v4.4.1) |
| **Data** | Synthetic retail sales dataset (200,000+ rows) — orders, products, customers, countries, revenue, cost, and profit fields |
| **Environment / Tooling** | Python venv, python-dotenv for config, Git/GitHub for version control |
| **Dev Environment** | Windows, PowerShell, VS Code |

---

## 📁 Project Structure

```
exasol-retail-insights/
├── data/
│   ├── load_data.py                # Loads generated CSV data into Exasol
│   └── generate_synthetic_data.py  # Generates the synthetic sales dataset
├── db/
│   ├── schema.sql                  # RETAIL.sales table definition
│   └── queries.sql                 # Reference/example SQL queries
├── backend/
│   ├── main.py                     # FastAPI app — /kpis /trend /top-products
│   │                                #   /restock-alerts /benchmark /ask
│   ├── llm_client.py               # Groq LLM client, NL-to-SQL prompt, SQL validator
│   ├── requirements.txt            # Backend dependencies
│   ├── .env                        # Real credentials (never committed)
│   └── .env.example                # Placeholder env file (safe to commit)
├── frontend/
│   ├── index.html                  # Dashboard UI
│   ├── style.css                   # Styling
│   └── app.js                      # Frontend logic + Chart.js visualizations
├── README.md
├── PITCH.md
└── .gitignore
```

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.12 (recommended — newer versions may lack compiled wheels for some dependencies)
- An [Exasol SaaS](https://cloud.exasol.com) database
- A [Groq API key](https://console.groq.com) (free tier)
- Git

### 1. Clone the repo

```bash
git clone https://github.com/satvika-davey/Exasol-Retail-Insights.git
cd Exasol-Retail-Insights/exasol-retail-insights
```

### 2. Set up the virtual environment

```bash
py -3.12 -m venv exasol
exasol\Scripts\activate        # Windows
pip install -r backend/requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` inside `backend/` and fill in:

```
EXASOL_HOST=your-exasol-host
EXASOL_PORT=8563
EXASOL_USER=your-username
EXASOL_PASSWORD=your-password
GROQ_API_KEY=your-groq-api-key
```

### 4. Create the schema

Open a Worksheet on [cloud.exasol.com](https://cloud.exasol.com), paste in the contents of `db/schema.sql`, and run it (tick **"Run all"** to execute the full multi-statement script).

### 5. Generate and load data

```bash
python data/generate_synthetic_data.py
python data/load_data.py
```

---

## ▶️ Running the App

### Run the backend

```bash
cd exasol-retail-insights
cd backend
exasol/Scripts/activate        # Windows
uvicorn main:app --reload --port 8000
```

### Run the frontend

No build step needed — it's plain HTML/CSS/JS.

```bash
cd exasol-retail-insights
cd frontend
python -m http.server 5500
```

Open `http://localhost:5500` in a browser.

---

## 💡 Example Questions to Ask

- "Which product has the highest profit margin?"
- "Which country has the highest number of orders?"
- "What were our top 5 products by revenue last month?"
- "Which products are at risk of stocking out?"
- "How does revenue this month compare to last month?"
- "What is basket analysis in retail?"
- "Explain the difference between gross margin and net margin"

---

## 🔒 Security Notes

- All LLM-generated SQL is validated against a table allowlist before execution — no destructive statements can run.
- Raw database errors (including host/connection details) are never sent to the client — only logged server-side.
- `.env` is git-ignored; only `.env.example` (placeholders) is committed.

---

## 🔮 Future Improvements

- **Multi-turn conversation memory** — let users ask follow-up questions (e.g. "now break that down by country") without repeating context.
- **Query result caching** — cache frequent question/SQL pairs to cut down on repeated LLM calls and speed up common lookups.
- **Role-based access** — restrict which tables/columns different user roles can query.
- **Anomaly detection** — proactively flag unusual sales dips/spikes instead of waiting for a question.
- **Export & sharing** — let users export chart/answer results as PDF or share a link to a specific query result.
- **Voice input** for the "Ask a Question" feature.
- **Broader dataset support** — allow uploading a store's own CSV/data instead of only the synthetic dataset.
- **Deployment on Exasol Personal** (AWS/Azure) for a fully self-hosted production version, beyond the current SaaS trial used for this submission.

---

## 👥 Team

**Team SAKS**

---

## 📌 Status

Built for the Exasol AI Build Challenge 2026. Core dashboard and NL-to-SQL engine are fully functional against live Exasol data.

---

## 📄 License

Built for the Exasol AI Build Challenge 2026 submission.
