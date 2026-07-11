import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "./Icon";
import type { ExploreRecipe } from "../types";
import { extractRecipe } from "../api";
import { addRecipe } from "../store";
import { onActivateKey } from "../helpers";

// Card for recipes already stored in the DB (from GET /recipes). These rows have
// no `id`, so opening one re-extracts by source_url (served from cache) to get a
// full Recipe, then navigates to its detail page — same flow as SimilarRecipeCard.
export function ExploreRecipeCard({ recipe }: { recipe: ExploreRecipe }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [imgFailed, setImgFailed] = useState(false);
  const showFallback = !recipe.image_url || imgFailed;

  const timeDisplay = recipe.total_time || recipe.cook_time || recipe.prep_time;

  const sourceDomain = (() => {
    try {
      return new URL(recipe.source_url).hostname.replace(/^www\./, "");
    } catch {
      return recipe.source_url;
    }
  })();

  async function handleClick() {
    if (loading) return;
    setLoading(true);
    try {
      const extracted = await extractRecipe(recipe.source_url);
      addRecipe(extracted);
      navigate(`/recipe/${extracted.id}`);
    } catch {
      setLoading(false);
    }
  }

  return (
    <div
      className="recipe-card"
      role="button"
      tabIndex={0}
      aria-label={`Open ${recipe.title}`}
      aria-busy={loading}
      onClick={handleClick}
      onKeyDown={onActivateKey(handleClick)}
      style={{
        opacity: loading ? "var(--opacity-disabled)" : 1,
        pointerEvents: loading ? "none" : "auto",
      }}
    >
      <div
        className={"recipe-thumb" + (showFallback ? " recipe-thumb-fallback" : "")}
      >
        {recipe.image_url && !imgFailed && (
          <img
            src={recipe.image_url}
            alt={recipe.title}
            width={400}
            height={300}
            loading="lazy"
            decoding="async"
            onError={() => setImgFailed(true)}
            className="recipe-thumb-img"
          />
        )}
        <span className="source">{sourceDomain}</span>
      </div>
      <div className="recipe-body">
        <div className="recipe-title">
          {loading ? "Extracting..." : recipe.title}
        </div>
        {timeDisplay && (
          <div className="recipe-meta">
            <span>
              <Icon name="clock" size={14} /> {timeDisplay}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
