# SousChat Frontend

The React client for [souschat.com](https://souschat.com). Paste a recipe URL, get back just the ingredients and steps.

Built with React 19, TypeScript, Vite, and plain CSS (with Tailwind available). Talks to the FastAPI backend in [../backend/](../backend/).

## Getting Started

Requires Node.js 18+.

```bash
npm install
npm run dev
```

The dev server runs at `http://localhost:5173`.

### Scripts

| Command           | What it does                                    |
| ----------------- | ----------------------------------------------- |
| `npm run dev`     | Start the Vite dev server with HMR              |
| `npm run build`   | Type-check with `tsc -b`, then build to `dist/` |
| `npm run preview` | Serve the production build locally              |
| `npm run lint`    | Run ESLint across the project                   |

## API Configuration

The backend base URL is a constant at the top of [src/api.ts](src/api.ts):

```ts
const API_BASE =
  "https://dashcook-api.happygrass-bd874e33.westus3.azurecontainerapps.io";
```

There is no `.env` file and no `import.meta.env` usage. To point the app at a local
backend, edit that constant to `http://localhost:8000` (and make sure `CORS_ORIGINS`
in `backend/.env` includes `http://localhost:5173`).

## Routes

Routes are declared in [src/App.tsx](src/App.tsx). Every page is lazy-loaded via
`React.lazy`, so each route ships as its own chunk.

| Path                   | Page                                             | Notes                                                          |
| ---------------------- | ------------------------------------------------ | -------------------------------------------------------------- |
| `/`                    | [Home](src/pages/Home.tsx)                       | URL input, recent and saved recipes, category shelves          |
| `/recipe/:id`          | [RecipeDetail](src/pages/RecipeDetail.tsx)       | Ingredients with serving scaler, steps, similar recipes        |
| `/cook/:id`            | [CookNow](src/pages/CookNow.tsx)                 | Distraction-free step view; hides the topbar, footer, and chat |
| `/explore/:categoryId` | [ExploreCategory](src/pages/ExploreCategory.tsx) | Paginated category browsing via cursor                         |
| `/tickets`             | [Tickets](src/pages/Tickets.tsx)                 | Admin view for submitted issue reports; hides footer and chat  |

Footer pages (about, privacy, and so on) render as overlays from
[FooterPages.tsx](src/pages/FooterPages.tsx) rather than as separate routes.

## Project Layout

```
src/
├── App.tsx                # Routes, theme state, saved-recipe state
├── main.tsx               # React entry point
├── api.ts                 # All backend calls, typed
├── store.ts               # localStorage recipe persistence
├── types.ts               # Shared interfaces (Recipe, Ingredient, Ticket, ...)
├── helpers.ts             # Quantity/time formatting, sessionStorage cache, a11y helpers
├── index.css              # Tailwind import plus the styles/ imports
├── components/            # Topbar, Footer, ChatWidget, cards, Toast, Icon
├── pages/                 # One file per route
├── hooks/
│   └── useClickSound.ts   # Global click sound, played from a pooled <audio>
├── data/
│   └── browseRecipes.ts   # Example recipe URL used by the empty-input path
└── styles/                # tokens.css plus one file per surface
public/                    # Favicon, SVG art, sounds, robots.txt, sitemap.xml
```

## State and Persistence

There is no state library. Everything lives in component state or browser storage:

- **`localStorage`**
  - `souschat.recipes` holds extracted recipes, most recent first, managed by [store.ts](src/store.ts)
  - `souschat.saved` holds an id-to-boolean map of saved recipes
  - `souschat.theme` holds the active theme name
  - `souschat.adminToken` holds the tickets admin token
- **`sessionStorage`** caches category and recipe list responses through
  `readSessionCache` / `writeSessionCache` in [helpers.ts](src/helpers.ts). It clears
  when the tab closes.

Every storage read and write is wrapped in try/catch, so private browsing and quota
errors degrade to a working app with no caching rather than a crash.

## Theming

Five themes ship: `cream` (default), `dark`, `calico`, `espresso`, and `noir`. All
of them are CSS custom property blocks in [src/styles/tokens.css](src/styles/tokens.css).
`App.tsx` applies the choice as a `theme-*` class on `<body>`; `cream` is the bare
`:root` block and gets no class. New themes only need a token block plus an entry in
the `THEMES` array and the `ThemeName` union in [types.ts](src/types.ts).

Styles are split by surface (`buttons.css`, `cards.css`, `cook-mode.css`, `chat.css`,
and so on) and pulled together by [src/index.css](src/index.css). Add new files to
that import list.

## Chat Widget

[ChatWidget.tsx](src/components/ChatWidget.tsx) switches behavior based on the route:

- On `/recipe/:id` it runs in **Q&A mode** and posts to `/ask` with the current
  recipe as context, keeping the last 8 turns of history.
- Everywhere else it runs in **search mode** and posts to `/discover`, which returns
  either AI-picked recipes with reasons (`mode: "ai"`) or plain semantic search
  results (`mode: "search"`) once the daily AI budget is spent.

Both endpoints share a daily per-IP budget. The widget reads the `remaining` count
off the response and shows a rate-limit message when it runs out.

## Build and Deploy

Deployed to Vercel using [vercel.json](vercel.json): build with `npm run build`,
serve `dist/`, and rewrite all paths to `index.html` so client-side routing works on
direct navigation and refresh.

React, React DOM, and React Router are split into a `vendor` chunk by the
`manualChunks` config in [vite.config.ts](vite.config.ts). Route-level code splitting
handles the rest.
