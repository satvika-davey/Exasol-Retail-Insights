# Retail/E-commerce Demand & Inventory Insights Platform

Built for the Exasol AI Build Challenge 2026. Ask natural-language
questions about sales/inventory data, get back KPI cards, charts,
and a sentence answer — powered by Exasol as the analytics database.
uyfhoifcxfghguif
## ⚠️ Read this before you sign up for anything

Exasol has **two** free hosted options and they are not interchangeable:

| Option | What it is | Can you load your own data? |
|---|---|---|
| **Exasol SaaS free trial** (`cloud.exasol.com/signup`) | You create a real, private database cluster in Exasol's cloud | **Yes** — this is what this project uses |
| **Public demo system** | A 30-day, static, shared demo with preloaded sample data | **No** — read-only shared environment, not for your own table |

Use the **SaaS trial**, not the public demo. If someone on the team
already signed up for the public demo thinking it was the same thing,
that's an hour lost re-signing-up — check this first thing this morning.

Also: a SaaS cluster takes **~15 minutes to provision** after you
create it, and **auto-stops after 120 minutes of inactivity** by default.
If the team breaks for lunch, expect the cluster to be stopped when you
come back — that's normal, not a bug, just restart it from the console.

## Setup — Exasol SaaS trial (Person 1, do this FIRST)

1. Go to `https://cloud.exasol.com/signup` and sign up with a work/college
   email if a personal one is rejected. Verify via the email you receive.
2. Sign in — you'll be prompted to add your first database. Pick any AWS
   region (closest to you is fine for a demo).
3. Wait for cluster status to go from "Creating" to ready (~15 min) —
   use this time to start on `db/schema.sql` and `data/generate_synthetic_data.py`.
4. From the database's connection page, copy: host, port (usually 8563),
   username, password. Put these into `backend/.env` (copy from `.env.example`).
5. Agree with the team on ONE schema name (`RETAIL`, already set as the
   default in `schema.sql` and `.env.example`) so nobody's test run
   collides with anyone else's.
6. Sanity-check the connection before building anything else:
   ```bash
   python -c "
   import pyexasol, os
   from dotenv import load_dotenv
   load_dotenv()
   c = pyexasol.connect(dsn=f'{os.environ[\"EXASOL_HOST\"]}:{os.environ[\"EXASOL_PORT\"]}',
                         user=os.environ['EXASOL_USER'], password=os.environ['EXASOL_PASSWORD'],
                         schema=os.environ.get('EXASOL_SCHEMA','RETAIL'), encryption=True)
   print(c.execute('SELECT 1').fetchone())
   "
   ```
   Keep this snippet handy — if the cluster auto-stops mid-hackathon,
   this is the fastest way to confirm "is it actually down" vs. a code bug.

## Load the schema and data

```bash
cd db
# run schema.sql against your Exasol instance (via the web SQL console,
# or via a quick pyexasol script — either works)

cd ../data
pip install -r ../backend/requirements.txt
python generate_synthetic_data.py        # only if you don't have a real CSV yet
python load_data.py synthetic_sales.csv  # or your real dataset's path
```

## Run the backend

```bash
cd exasol-retail-insights
cd backend
exasol\Scripts\activate        # Windows
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/health` — should return `{"status": "ok"}`.

## Run the frontend

No build step needed — it's plain HTML/CSS/JS.

```bash
cd exasol-retail-insights
cd frontend
python -m http.server 5500
```

Open `http://localhost:5500` in a browser. The frontend expects the
backend at `http://localhost:8000` (see `API_BASE` in `app.js`).

## Environment variables

See `backend/.env.example` for the full list. You need Exasol
connection details plus one LLM provider key (Groq recommended —
fast, free tier, no CUDA/GPU setup required on any teammate's laptop).

## Project structure

```
exasol-retail-insights/
├── data/
│   ├── load_data.py
│   └── generate_synthetic_data.py
├── db/
│   ├── schema.sql
│   └── queries.sql
├── backend/
│   ├── main.py
│   ├── llm_client.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── PITCH.md
└── README.md
```

## Known risks (read before demo day)

- **Free LLM APIs rate-limit.** If all 4 of you hit `/ask` at once near
  demo time, expect throttling. Stagger testing; only re-run the final
  demo questions once, right before presenting.
- **The NL-to-SQL feature is the least predictable part of this app.**
  Don't build your live demo around trusting it blind — the 3–4 example
  question buttons in the frontend exist as a guaranteed-working fallback.
- **SQL safety is non-negotiable.** `main.py`'s `validate_sql()` blocks
  DDL/DML keywords AND restricts queries to the `sales` table only —
  don't remove either check to save time.
- Git from the start. Four people editing the same files without version
  control is how hours get lost at 6pm.
- Never commit `.env` — only `.env.example`. Add `.env` to `.gitignore`.
