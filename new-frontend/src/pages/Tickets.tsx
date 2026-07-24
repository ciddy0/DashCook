import { useState, useEffect, useCallback, useRef } from "react";
import { Icon } from "../components/Icon";
import { listTickets, UNAUTHORIZED } from "../services";
import { shelfColor } from "../utils";
import type { TicketDetail, TicketCategory, TicketStatus } from "../types";

const PAGE_LIMIT = 20;
const TOKEN_KEY = "souschat.adminToken";

// Results per filter combination, kept in memory only: flipping between filters
// replays a previous fetch, while a page reload starts from a clean slate.
type CacheEntry = { items: TicketDetail[]; total: number; offset: number };
const resultCache = new Map<string, CacheEntry>();

const STATUSES: TicketStatus[] = ["open", "in_progress", "resolved", "closed"];
const CATEGORIES: TicketCategory[] = [
  "parser",
  "recipe",
  "account",
  "bug",
  "feature_request",
  "other",
];

const STATUS_TONE: Record<TicketStatus, string> = {
  open: "tk-tone-info",
  in_progress: "tk-tone-warning",
  resolved: "tk-tone-success",
  closed: "tk-tone-muted",
};

function label(v: string): string {
  return v.replace(/_/g, " ");
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
}

// Same shelf cards the pantry uses to pick a recipe category, with an "all"
// shelf up front to clear the filter.
function ShelfFilter<T extends string>({
  heading,
  options,
  selected,
  allLabel,
  onSelect,
}: {
  heading: string;
  options: readonly T[];
  selected: T | "";
  allLabel: string;
  onSelect: (v: T | "") => void;
}) {
  return (
    <div className="tk-filter-group">
      <span className="eyebrow">{heading}</span>
      <div className="explore-shelves">
        <button
          className={
            "card card-hover explore-shelf" + (selected === "" ? " is-active" : "")
          }
          aria-pressed={selected === ""}
          onClick={() => onSelect("")}
        >
          <span
            className="explore-shelf-swatch"
            style={{ background: "var(--cat-neutral)" }}
          />
          <span className="explore-shelf-name">{allLabel}</span>
        </button>
        {options.map((o, idx) => (
          <button
            key={o}
            className={
              "card card-hover explore-shelf" + (selected === o ? " is-active" : "")
            }
            aria-pressed={selected === o}
            onClick={() => onSelect(selected === o ? "" : o)}
          >
            <span
              className="explore-shelf-swatch"
              style={{ background: shelfColor(idx, o) }}
            />
            <span className="explore-shelf-name">{label(o)}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export function Tickets() {
  const [token, setToken] = useState<string>(
    () => sessionStorage.getItem(TOKEN_KEY) ?? "",
  );
  const [tokenInput, setTokenInput] = useState("");

  const [items, setItems] = useState<TicketDetail[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [status, setStatus] = useState<TicketStatus | "">("");
  const [category, setCategory] = useState<TicketCategory | "">("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // Debounce the free-text search so we don't refetch on every keystroke.
  useEffect(() => {
    const id = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(id);
  }, [search]);

  const cacheKey = `${status}|${category}|${debouncedSearch}`;

  // Identifies the fetch (or cache hit) that currently owns the list. A slow
  // response the user has already filtered away from still gets cached, but it
  // no longer renders and no longer speaks for the loading state.
  const reqId = useRef(0);

  const lock = useCallback(() => {
    sessionStorage.removeItem(TOKEN_KEY);
    resultCache.clear();
    setToken("");
    setItems([]);
    setTotal(0);
    setOffset(0);
    setError(null);
  }, []);

  const load = useCallback(
    async (nextOffset: number) => {
      if (!token) return;
      const id = ++reqId.current;
      setLoading(true);
      setError(null);
      try {
        const res = await listTickets({
          token,
          limit: PAGE_LIMIT,
          offset: nextOffset,
          status: status || undefined,
          category: category || undefined,
          search: debouncedSearch || undefined,
        });
        // Page 0 is always cached before "Load more" is reachable, so the cache
        // holds the pages already on screen.
        const seen = resultCache.get(cacheKey)?.items ?? [];
        const next = nextOffset ? [...seen, ...res.items] : res.items;
        resultCache.set(cacheKey, {
          items: next,
          total: res.total,
          offset: nextOffset,
        });
        if (reqId.current !== id) return;
        setItems(next);
        setTotal(res.total);
        setOffset(nextOffset);
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Something went wrong.";
        if (msg === UNAUTHORIZED) {
          // Bad/expired token — kick back to the gate with a hint.
          sessionStorage.removeItem(TOKEN_KEY);
          resultCache.clear();
          setToken("");
          setError("That token was rejected. Try again.");
        } else if (reqId.current === id) {
          setError(msg);
        }
      } finally {
        if (reqId.current === id) setLoading(false);
      }
    },
    [token, status, category, debouncedSearch, cacheKey],
  );

  // Switching filters replays the cached page when we've already fetched it;
  // otherwise it's a fresh query from the top.
  useEffect(() => {
    if (!token) return;
    const hit = resultCache.get(cacheKey);
    if (hit) {
      // Take ownership so any fetch still in flight resolves into nothing.
      reqId.current += 1;
      /* eslint-disable react-hooks/set-state-in-effect -- hydrate synchronously from cache to avoid a loading flash */
      setItems(hit.items);
      setTotal(hit.total);
      setOffset(hit.offset);
      setLoading(false);
      setError(null);
      /* eslint-enable react-hooks/set-state-in-effect */
      return;
    }
    setItems([]);
    load(0);
  }, [token, cacheKey, load]);

  function unlock(e: React.FormEvent) {
    e.preventDefault();
    const t = tokenInput.trim();
    if (!t) return;
    sessionStorage.setItem(TOKEN_KEY, t);
    setError(null);
    setTokenInput("");
    setToken(t);
  }

  // --- Gate ---------------------------------------------------------------
  if (!token) {
    return (
      <div className="page">
        <div
          className="card"
          style={{ maxWidth: 420, margin: "48px auto", textAlign: "center" }}
        >
          <div className="tk-lock-badge">
            <Icon name="bookmark-fill" size={22} />
          </div>
          <h2 style={{ fontSize: 24, fontWeight: 600, marginBottom: 6 }}>
            Tickets
          </h2>
          <p
            style={{
              color: "var(--text-2)",
              fontWeight: 500,
              marginBottom: 20,
            }}
          >
            Enter your admin token to view submitted tickets.
          </p>

          {error && (
            <div
              className="banner banner-warning"
              style={{ textAlign: "left", marginBottom: 16 }}
            >
              <span>{error}</span>
            </div>
          )}

          <form
            onSubmit={unlock}
            style={{ display: "flex", flexDirection: "column", gap: 12 }}
          >
            <input
              className="input"
              type="password"
              autoFocus
              placeholder="Admin token"
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
            />
            <button className="btn" type="submit" disabled={!tokenInput.trim()}>
              Unlock
            </button>
          </form>
        </div>
      </div>
    );
  }

  // --- List ---------------------------------------------------------------
  const hasMore = items.length < total;

  return (
    <div className="page">
      <div className="section-header">
        <h2>Tickets</h2>
        <span className="eyebrow">
          {total} {total === 1 ? "ticket" : "tickets"}
        </span>
      </div>

      <div className="tk-filters">
        <div className="tk-search">
          <Icon name="search" size={16} />
          <input
            className="input"
            type="search"
            placeholder="Search subject or description…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button className="btn btn-secondary btn-sm" onClick={lock}>
          Lock
        </button>
      </div>

      <ShelfFilter
        heading="Status"
        options={STATUSES}
        selected={status}
        allLabel="All status"
        onSelect={setStatus}
      />

      <ShelfFilter
        heading="Category"
        options={CATEGORIES}
        selected={category}
        allLabel="All categories"
        onSelect={setCategory}
      />

      {error && (
        <div className="banner banner-warning" style={{ marginBottom: 16 }}>
          <span>{error}</span>
        </div>
      )}

      {items.length === 0 && !loading ? (
        <div className="card empty-state">
          <h3>No tickets here</h3>
          <p>Nothing matches these filters yet.</p>
        </div>
      ) : (
        <div className="tk-list">
          {items.map((t) => (
            <article key={t.id} className="card tk-card">
              <div className="tk-card-head">
                <h3 className="tk-subject">{t.subject}</h3>
                <div className="tk-badges">
                  <span className={"tk-badge " + STATUS_TONE[t.status]}>
                    {label(t.status)}
                  </span>
                  <span className="tk-badge tk-tone-neutral">
                    {label(t.category)}
                  </span>
                </div>
              </div>

              <p className="tk-desc">{t.description}</p>

              <div className="tk-card-foot">
                {t.recipe_url && (
                  <a
                    className="tk-link"
                    href={t.recipe_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Icon name="link" size={14} /> Recipe URL
                  </a>
                )}
                <span className="tk-date">{formatDate(t.created_at)}</span>
              </div>
            </article>
          ))}
        </div>
      )}

      {hasMore && (
        <div style={{ textAlign: "center", marginTop: 32 }}>
          <button
            className="btn btn-secondary"
            disabled={loading}
            onClick={() => load(offset + PAGE_LIMIT)}
          >
            {loading ? "Loading…" : "Load more"}
          </button>
        </div>
      )}
    </div>
  );
}
