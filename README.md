# SousChat

Extract clean, structured recipes from bloated recipe websites.

Paste a URL, get the recipe — no ads, no life stories, no popups. SousChat scrapes recipe pages, parses ingredients into structured data with scaling support, and uses vector embeddings for semantic search and similar recipe discovery.

**Live at [souschat.com](https://souschat.com)**

## Features

- **Recipe extraction** — paste any recipe URL and get a clean, structured recipe via JSON-LD parsing
- **Ingredient parsing** — quantities, units, and names broken out with support for fractions, ranges, and scaling
- **Semantic search** — find recipes by description using OpenAI embeddings and pgvector cosine similarity
- **AI recipe discovery** — describe a mood ("cozy warm dinners") and Claude picks recipes from the search results and says why each fits, falling back to plain semantic search once the daily limit is spent
- **Similar recipes** — discover related recipes based on title and ingredient embeddings
- **Cook mode** — distraction-free step-by-step view for following along while cooking
- **Offline saves** — save recipes to localStorage, no account required

## Tech Stack

| Backend | Frontend |
|---|---|
| FastAPI | React 19 |
| asyncpg | TypeScript |
| pgvector (PostgreSQL 16) | Tailwind CSS 4 |
| OpenAI (`text-embedding-3-large`) | Vite |
| httpx + cloudscraper | React Router |
| BeautifulSoup4 | |

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (for PostgreSQL + pgvector)
- An [OpenAI API key](https://platform.openai.com/api-keys)

### Backend

```bash
# Start PostgreSQL with pgvector
cd backend
docker compose up -d

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # then edit with your values
```

Required environment variables (set in `backend/.env`):

```
DATABASE_URL=postgresql://dashcook:dashcook@localhost:5433/dashcook
OPENAI_API_KEY=your-key-here
CORS_ORIGINS=http://localhost:5173
RATE_LIMIT=30
```

```bash
# Run database migrations
# Apply SQL files in backend/db/migrations/ in order

# Start the server
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend

```bash
cd new-frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

## API Reference

### `POST /url`

Extract a recipe from a URL. Rate limited to 30 requests/hour per IP.

**Request:**
```json
{
  "url": "https://example.com/some-recipe"
}
```

**Response:**
```json
{
  "title": "Spaghetti Carbonara",
  "source_url": "https://example.com/some-recipe",
  "image_url": "https://example.com/image.jpg",
  "prep_time": "10 minutes",
  "cook_time": "20 minutes",
  "total_time": "30 minutes",
  "servings": "4",
  "ingredients": [
    {
      "raw": "2 cups all-purpose flour",
      "name": "all-purpose flour",
      "quantity": 2.0,
      "quantity_max": null,
      "unit": "cup",
      "scalable": true
    }
  ],
  "instructions": ["Boil salted water...", "Cook the pasta..."]
}
```

### `GET /similar?url={source_url}&limit={n}`

Find similar recipes by cosine distance on embeddings. Returns up to 20 results (default 5).

**Response:**
```json
[
  {
    "title": "Pasta Primavera",
    "source_url": "https://example.com/pasta-primavera",
    "image_url": "https://example.com/img.jpg",
    "distance": 0.123
  }
]
```

### `GET /search?q={query}&limit={n}`

Semantic search across all stored recipes. Rate limited to 30 requests/hour per IP. Returns up to 50 results (default 10).

Response shape is the same as `/similar`.

### `POST /discover`

Retrieval-augmented recipe discovery: semantic search retrieves a shortlist of 20 recipes, then Claude picks the ones that fit the query and explains why.

Draws on a shared daily AI budget (5/day per IP, also spent by `/ask`). When that budget is gone — or the assistant is unavailable, or nothing on the shortlist fits — the endpoint **falls back to plain semantic search** rather than failing, and reports which path it took via `mode`.

**Request:**
```json
{ "query": "cozy warm dinners", "limit": 5 }
```

**Response:**
```json
{
  "mode": "ai",
  "answer": "For a cozy night in, these all lean slow-cooked and rich:",
  "recipes": [
    {
      "title": "Beef Bourguignon",
      "source_url": "https://example.com/beef-bourguignon",
      "image_url": "https://example.com/img.jpg",
      "total_time": "3 hours",
      "why": "Braises for three hours in red wine — about as warming as dinner gets."
    }
  ],
  "remaining": 4
}
```

`mode` is `"ai"` when Claude made the picks and `"search"` when it fell back (in which case `answer` and every `why` are `null`). `remaining` is the caller's AI requests left today.

## Project Structure

```
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Environment/settings (pydantic-settings)
│   ├── routes/
│   │   ├── health.py           # GET /, GET /ping
│   │   └── recipes.py          # POST /url, POST /ask, POST /discover, GET /similar, GET /search
│   ├── models/
│   │   ├── recipes.py          # Recipe, Ingredient, SimilarRecipe
│   │   └── requests.py         # ExtractRequest
│   ├── services/
│   │   ├── recipe_service.py   # Orchestration: scrape → parse → embed → cache
│   │   ├── scraper.py          # HTTP fetching with cloudscraper fallback
│   │   ├── parser.py           # JSON-LD schema.org/Recipe extraction
│   │   ├── embedder.py         # OpenAI embedding generation
│   │   ├── recipe_qa.py        # Claude Q&A about one recipe
│   │   ├── recipe_discovery.py # Claude picks recipes from search results (RAG)
│   │   └── ingredient_parser.py
│   ├── db/
│   │   ├── pool.py             # asyncpg connection pool
│   │   ├── recipes.py          # Query functions
│   │   └── migrations/         # SQL migration files
│   ├── middleware/
│   │   ├── rate_limiter.py     # IP-based sliding window rate limiter
│   │   └── ai_quota.py         # Shared daily budget for the Claude endpoints
│   └── tests/
├── new-frontend/
│   ├── src/
│   │   ├── App.tsx             # Routes: /, /recipe/:id, /cook/:id
│   │   ├── api.ts              # API client
│   │   ├── store.ts            # localStorage persistence
│   │   ├── components/         # Topbar, Footer, RecipeCard, etc.
│   │   ├── pages/              # Home, RecipeDetail, CookNow
│   │   └── styles/             # CSS modules and tokens
│   └── vite.config.ts
├── .github/workflows/
│   └── deploy.yml              # CI/CD: test → build → deploy
└── LICENSE                     # MIT
```

## Deployment

The backend deploys to **Azure Container Apps** via GitHub Actions CI/CD:

1. **Test** — runs `pytest` against the backend test suite
2. **Build** — builds a Docker image and pushes to Azure Container Registry
3. **Deploy** — updates the Azure Container App with the new image

The frontend is deployed as a static site.

The pipeline triggers on pushes to `main` that modify files under `backend/` or the workflow file itself.

## License

[MIT](LICENSE)
