import { useState, useEffect, useCallback, useRef } from "react";
import { Icon } from "../components/Icon";
import { listTickets, updateTicket, UNAUTHORIZED } from "../services";
import { useToast } from "../context/toast-context";
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

// One icon per stop on the status path, so a node reads as a state before its
// label does.
const STATUS_ICON: Record<TicketStatus, string> = {
  open: "flag",
  in_progress: "play",
  resolved: "check",
  closed: "minus",
};

function label(v: string): string {
  return v.replace(/_/g, " ");
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
}

// Compact chip row with an "all" chip up front to clear the filter. These used
// to be pantry shelf cards, which reserve two text lines each and pushed the
// list itself below the fold for the sake of eleven one-word options.
function ChipFilter<T extends string>({
  heading,
  options,
  selected,
  allLabel,
  dotClass,
  dotColor,
  onSelect,
}: {
  heading: string;
  options: readonly T[];
  selected: T | "";
  allLabel: string;
  // A chip's dot takes its color from --tone (set by a class) or from an
  // explicit swatch; status uses the former so it matches the track below.
  dotClass?: (o: T) => string;
  dotColor?: (o: T, idx: number) => string;
  onSelect: (v: T | "") => void;
}) {
  return (
    <div className="tk-filter-group">
      <span className="eyebrow">{heading}</span>
      <div className="chip-row" role="group" aria-label={heading}>
        <button
          type="button"
          className={"chip tk-chip" + (selected === "" ? " is-active" : "")}
          aria-pressed={selected === ""}
          onClick={() => onSelect("")}
        >
          {allLabel}
        </button>
        {options.map((o, idx) => (
          <button
            key={o}
            type="button"
            className={
              "chip tk-chip " +
              (dotClass?.(o) ?? "") +
              (selected === o ? " is-active" : "")
            }
            aria-pressed={selected === o}
            onClick={() => onSelect(selected === o ? "" : o)}
          >
            <span
              className="tk-chip-dot"
              style={dotColor ? { background: dotColor(o, idx) } : undefined}
            />
            {label(o)}
          </button>
        ))}
      </div>
    </div>
  );
}

// Inline status editor, shaped like a lesson path: the four statuses are stops
// on a track, every node up to the current one is filled in that status's tone,
// and the rest sit hollow ahead of it. So the card's state is legible from the
// fill alone, and any node is still one tap away — forward or back.
function StatusTrack({
  ticket,
  saving,
  busy,
  onChange,
}: {
  ticket: TicketDetail;
  saving: boolean;
  // Some other ticket is mid-write. Only one save runs at a time, so the nodes
  // are inert until it lands rather than silently swallowing the tap.
  busy: boolean;
  onChange: (next: TicketStatus) => void;
}) {
  const current = STATUSES.indexOf(ticket.status);
  return (
    <div
      className={
        `tk-track tk-st-${ticket.status}` + (saving ? " is-saving" : "")
      }
      role="group"
      aria-label={`Status for “${ticket.subject}”`}
      aria-busy={saving}
    >
      {STATUSES.map((s, i) => (
        <button
          key={s}
          type="button"
          className={
            "tk-node " +
            (i < current ? "is-done" : i === current ? "is-current" : "is-todo")
          }
          aria-pressed={i === current}
          disabled={saving || busy}
          onClick={() => onChange(s)}
        >
          <span className="tk-node-dot">
            <Icon name={STATUS_ICON[s]} size={18} />
          </span>
          <span className="tk-node-label">{label(s)}</span>
        </button>
      ))}
    </div>
  );
}

export function Tickets() {
  const toast = useToast();
  const [token, setToken] = useState<string>(
    () => sessionStorage.getItem(TOKEN_KEY) ?? "",
  );
  const [tokenInput, setTokenInput] = useState("");

  const [items, setItems] = useState<TicketDetail[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Ticket currently being written to the server; its picker is locked so a
  // second tap can't race the first.
  const [savingId, setSavingId] = useState<string | null>(null);

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

  // A rejected token drops us back to the gate with everything cleared.
  const rejectToken = useCallback(() => {
    sessionStorage.removeItem(TOKEN_KEY);
    resultCache.clear();
    setToken("");
    setError("That token was rejected. Try again.");
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
          rejectToken();
        } else if (reqId.current === id) {
          setError(msg);
        }
      } finally {
        if (reqId.current === id) setLoading(false);
      }
    },
    [token, status, category, debouncedSearch, cacheKey, rejectToken],
  );

  // Writes the new status through, painting it immediately and rolling back if
  // the server refuses.
  async function changeStatus(ticket: TicketDetail, next: TicketStatus) {
    if (savingId || ticket.status === next) return;

    const before = items;
    setSavingId(ticket.id);
    setError(null);
    setItems(items.map((t) => (t.id === ticket.id ? { ...t, status: next } : t)));

    try {
      const saved = await updateTicket({ token, id: ticket.id, status: next });

      // Every other filter's cached page may now hold this ticket under its old
      // status, so drop them; the current view is rewritten in place below.
      for (const key of resultCache.keys()) {
        if (key !== cacheKey) resultCache.delete(key);
      }

      // Under an active status filter the ticket has just filtered itself out.
      const drops = status !== "" && saved.status !== status;
      const nextItems = drops
        ? before.filter((t) => t.id !== saved.id)
        : before.map((t) => (t.id === saved.id ? saved : t));
      const nextTotal = drops ? Math.max(0, total - 1) : total;

      setItems(nextItems);
      setTotal(nextTotal);
      resultCache.set(cacheKey, {
        items: nextItems,
        total: nextTotal,
        offset,
      });
      toast.success(`Marked “${ticket.subject}” as ${label(next)}.`);
    } catch (e) {
      setItems(before);
      const msg = e instanceof Error ? e.message : "Something went wrong.";
      if (msg === UNAUTHORIZED) {
        rejectToken();
      } else {
        toast.warning(msg);
      }
    } finally {
      setSavingId(null);
    }
  }

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

      <ChipFilter
        heading="Status"
        options={STATUSES}
        selected={status}
        allLabel="All status"
        dotClass={(s) => `tk-st-${s}`}
        onSelect={setStatus}
      />

      <ChipFilter
        heading="Category"
        options={CATEGORIES}
        selected={category}
        allLabel="All categories"
        dotColor={(o, idx) => shelfColor(idx, o)}
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
                  <span className="tk-badge tk-tone-neutral">
                    {label(t.category)}
                  </span>
                </div>
              </div>

              <p className="tk-desc">{t.description}</p>

              <StatusTrack
                ticket={t}
                saving={savingId === t.id}
                busy={savingId !== null && savingId !== t.id}
                onChange={(next) => changeStatus(t, next)}
              />

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
