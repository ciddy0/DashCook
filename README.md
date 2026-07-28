# souschat

> Extract clean, structured recipes from bloated recipe websites.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![Postgres](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

**Live at [souschat.com](https://souschat.com)**

Paste a recipe URL, get the recipe: no ads, no life stories, no pop-ups. souschat scrapes
recipe pages, parses ingredients into structured, scalable data, and stores everything with
vector embeddings so recipes can be searched by meaning rather than keywords.

---

## What it does

- **Recipe extraction**: any recipe URL in, clean structured JSON out
- **Ingredient parsing**: quantities, units, and names split apart, with scaling for serving sizes
- **Semantic search**: find recipes by describing them, backed by OpenAI embeddings and pgvector
- **Similar recipes**: related recipes surfaced by embedding distance
- **AI discovery**: describe a mood ("cozy warm dinners") and Claude picks from real search results, with a line on why each fits
- **Recipe Q&A**: ask about substitutions, timing, or storage for the recipe you're cooking
- **Automatic categories**: recipes are clustered and each cluster is named by an LLM
- **Cook mode**: distraction-free, step-by-step view for actually cooking
- **Offline saves**: recipes persist to `localStorage`, no account required

Every AI feature degrades gracefully. When the daily budget is spent or a provider is
unavailable, the app falls back to plain semantic search instead of failing.

---

## Architecture

```
                 ┌──────────────────────┐
   browser  ───► │  React 19 SPA        │   Vercel
                 │  Vite · TypeScript   │
                 └──────────┬───────────┘
                            │  HTTPS / JSON
                            ▼
                 ┌──────────────────────┐
                 │  FastAPI service     │   Azure Container Apps
                 │  scrape · parse ·    │
                 │  embed · retrieve    │
                 └──┬────────┬───────┬──┘
                    │        │       │
      recipe pages ◄┘        │       └► OpenAI    (embeddings, cluster naming)
      (httpx /              │           Anthropic (discovery, recipe Q&A)
       cloudscraper)        ▼
                 ┌──────────────────────┐
                 │  PostgreSQL 16       │
                 │  + pgvector          │
                 └──────────────────────┘
```

A single monorepo holds both halves. The frontend is a static SPA with no server of its
own; all data, caching, rate limiting, and AI orchestration live in the backend.

---

## Repository layout

| Path                                     | What it is                                                               |
| ---------------------------------------- | ------------------------------------------------------------------------ |
| [backend/](backend/)                     | FastAPI service: scraping, parsing, embeddings, RAG endpoints, Postgres   |
| [new-frontend/](new-frontend/)           | React 19 + Vite client, deployed to Vercel. **The active frontend.**      |
| [frontend/](frontend/)                   | Earlier frontend iteration, kept for reference. No longer deployed.       |
| [.github/workflows/](.github/workflows/) | CI/CD pipeline for the backend                                           |

Each half documents itself in depth:

- **[backend/README.md](backend/README.md)**: full API reference, architecture, environment variables, rate limiting, data model, migrations, and maintenance scripts
- **[new-frontend/README.md](new-frontend/README.md)**: routes, project layout, state and persistence, theming, and build/deploy

---

## Tech stack

| Layer      | Stack                                                                     |
| ---------- | ------------------------------------------------------------------------- |
| Frontend   | React 19 · TypeScript · Vite · React Router · CSS custom properties        |
| Backend    | Python 3.11 · FastAPI · Uvicorn · asyncpg · BeautifulSoup · slowapi        |
| Data       | PostgreSQL 16 · pgvector (3072-dim embeddings)                             |
| AI         | OpenAI (`text-embedding-3-large`) · Anthropic Claude (`claude-haiku-4-5`)  |
| Infra      | Docker · Azure Container Apps · Vercel · GitHub Actions                    |

---

## Quick start

**Prerequisites:** Python 3.11, Node.js 18+, Docker, and an [OpenAI API key](https://platform.openai.com/api-keys).
An [Anthropic API key](https://console.anthropic.com/) is optional and only needed for the AI features.

```bash
# 1. Backend: database, dependencies, config
cd backend
docker compose up -d                      # Postgres 16 + pgvector on :5433
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
                                          # create backend/.env with your keys
                                          # (see the backend README for every setting)

for f in db/migrations/*.sql; do          # apply migrations in order
  psql "postgresql://dashcook:dashcook@localhost:5433/dashcook" -f "$f"
done

uvicorn main:app --reload                 # API on http://localhost:8000

# 2. Frontend (in a second terminal)
cd new-frontend
npm install
npm run dev                               # app on http://localhost:5173
```

Interactive API docs are served at <http://localhost:8000/docs>.

To point the client at your local API, edit `API_BASE` in
[new-frontend/src/api.ts](new-frontend/src/api.ts) and make sure `CORS_ORIGINS` in
`backend/.env` includes `http://localhost:5173`. See the
[backend README](backend/README.md#environment-variables) for the full list of settings.

---

## Testing

```bash
cd backend && pytest       # ingredient parsing, pagination, categories,
                           # rate limiting, tickets, RAG discovery
cd new-frontend && npm run lint
```

No test makes a live call to OpenAI or Anthropic. Both are stubbed.

---

## Deployment

- **Backend**: every push to `main` touching `backend/**` triggers
  [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml), which runs `pytest`, builds
  and pushes a Docker image to Azure Container Registry, then deploys to Azure Container Apps.
- **Frontend**: built with Vite and served as a static site on Vercel, with all paths
  rewritten to `index.html` for client-side routing.

---

## License

[MIT](LICENSE)
