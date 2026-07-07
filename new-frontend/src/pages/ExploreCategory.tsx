import { useState, useEffect, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { Icon } from "../components/Icon";
import { ExploreRecipeCard } from "../components/ExploreRecipeCard";
import { listCategories, listRecipes } from "../api";
import type { ExploreRecipe } from "../types";

const PAGE_LIMIT = 20;

export function ExploreCategory() {
  const { categoryId } = useParams<{ categoryId: string }>();
  const category = categoryId ? parseInt(categoryId, 10) : NaN;

  const [name, setName] = useState<string>("");
  const [items, setItems] = useState<ExploreRecipe[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);

  // Resolve the shelf name for the heading.
  useEffect(() => {
    if (Number.isNaN(category)) return;
    let alive = true;
    listCategories().then((cats) => {
      if (alive) setName(cats.find((c) => c.id === category)?.name ?? "");
    });
    return () => {
      alive = false;
    };
  }, [category]);

  const loadPage = useCallback(
    async (nextCursor: string | null) => {
      setLoading(true);
      const res = await listRecipes({
        category,
        limit: PAGE_LIMIT,
        cursor: nextCursor,
      });
      setItems((prev) => (nextCursor ? [...prev, ...res.items] : res.items));
      setCursor(res.next_cursor);
      setHasMore(res.next_cursor != null);
      setLoading(false);
    },
    [category],
  );

  // Initial load (and reset) when the category changes.
  useEffect(() => {
    if (Number.isNaN(category)) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- reset the list when switching shelves before the new page loads
    setItems([]);
    setCursor(null);
    loadPage(null);
  }, [category, loadPage]);

  return (
    <div className="page">
      <div style={{ marginBottom: 20 }}>
        <Link to="/" className="btn btn-secondary btn-sm">
          <Icon name="arrow-l" size={14} /> Back to pantry
        </Link>
      </div>

      <div className="section-header">
        <h2>{name || "Shelf"}</h2>
        {items.length > 0 && (
          <span className="eyebrow">
            {items.length}
            {hasMore ? "+" : ""} recipes
          </span>
        )}
      </div>

      {items.length === 0 && !loading ? (
        <div className="card empty-state">
          <h3>Nothing on this shelf yet</h3>
          <p>Extract a few recipes and they'll get sorted onto shelves here.</p>
        </div>
      ) : (
        <div className="recipe-grid">
          {items.map((r) => (
            <ExploreRecipeCard key={r.source_url} recipe={r} />
          ))}
        </div>
      )}

      {hasMore && (
        <div style={{ textAlign: "center", marginTop: 32 }}>
          <button
            className="btn btn-secondary"
            disabled={loading}
            onClick={() => loadPage(cursor)}
          >
            {loading ? "Loading…" : "Load more"}
          </button>
        </div>
      )}
    </div>
  );
}
