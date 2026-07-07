import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Icon } from "./Icon";
import { ExploreRecipeCard } from "./ExploreRecipeCard";
import { listCategories, listRecipes } from "../api";
import {
  shelfColor,
  onActivateKey,
  readSessionCache,
  writeSessionCache,
} from "../helpers";
import type { Category, ExploreRecipe } from "../types";

const PREVIEW_LIMIT = 4;

export function ExplorePantry() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [preview, setPreview] = useState<ExploreRecipe[]>([]);
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => {
    let alive = true;
    listCategories().then((cats) => {
      if (alive) setCategories(cats);
    });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (selectedId == null) return;

    // Serve a previously-fetched shelf straight from sessionStorage — no request,
    // no loading flash. Cache lives until the tab closes.
    const cacheKey = `explore:recipes:${selectedId}:${PREVIEW_LIMIT}`;
    const cached = readSessionCache<ExploreRecipe[]>(cacheKey);
    if (cached) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- hydrate synchronously from cache to avoid a loading flash
      setPreview(cached);
      setPreviewLoading(false);
      return;
    }

    let alive = true;
    setPreviewLoading(true);
    listRecipes({ category: selectedId, limit: PREVIEW_LIMIT })
      .then((res) => {
        if (!alive) return;
        setPreview(res.items);
        writeSessionCache(cacheKey, res.items);
      })
      .finally(() => {
        if (alive) setPreviewLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [selectedId]);

  // Nothing to show until the shelves load.
  if (categories.length === 0) return null;

  const selected = categories.find((c) => c.id === selectedId) ?? null;

  return (
    <section className="explore-pantry">
      <div className="section-header">
        <h2>Explore the pantry</h2>
        <span className="eyebrow">{categories.length} shelves</span>
      </div>
      <p className="explore-intro">
        Every recipe you and other cooks have extracted, sorted onto shelves by souschat. Tap a shelf to browse.
      </p>

      <div className="explore-shelves">
        {categories.map((cat) => {
          const active = cat.id === selectedId;
          return (
            <div
              key={cat.id}
              className={"card card-hover explore-shelf" + (active ? " is-active" : "")}
              role="button"
              tabIndex={0}
              aria-pressed={active}
              aria-label={`Browse ${cat.name}`}
              onClick={() => setSelectedId(active ? null : cat.id)}
              onKeyDown={onActivateKey(() => setSelectedId(active ? null : cat.id))}
            >
              <span
                className="explore-shelf-swatch"
                style={{ background: shelfColor(cat.id) }}
              />
              <div className="explore-shelf-name">{cat.name}</div>
            </div>
          );
        })}
      </div>

      {selected && (
        <div className="explore-preview">
          <div className="section-header">
            <h2>{selected.name}</h2>
            <Link to={`/explore/${selected.id}`} className="btn btn-secondary btn-sm">
              See all <Icon name="arrow-r" size={14} />
            </Link>
          </div>
          {previewLoading ? (
            <div className="card empty-state">
              <p>Loading recipes…</p>
            </div>
          ) : preview.length === 0 ? (
            <div className="card empty-state">
              <p>No recipes on this shelf yet.</p>
            </div>
          ) : (
            <div className="recipe-grid">
              {preview.map((r) => (
                <ExploreRecipeCard key={r.source_url} recipe={r} />
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
