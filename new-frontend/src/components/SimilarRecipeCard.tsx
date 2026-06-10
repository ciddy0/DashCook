import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { SimilarRecipe } from "../types";
import { extractRecipe } from "../api";
import { addRecipe } from "../store";

export function SimilarRecipeCard({ recipe }: { recipe: SimilarRecipe }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [imgFailed, setImgFailed] = useState(false);
  const showFallback = !recipe.image_url || imgFailed;

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
      onClick={handleClick}
      style={{ opacity: loading ? 0.6 : 1, pointerEvents: loading ? "none" : "auto" }}
    >
      <div
        className={"recipe-thumb" + (showFallback ? " recipe-thumb-fallback" : "")}
      >
        {recipe.image_url && !imgFailed && (
          <img
            src={recipe.image_url}
            alt={recipe.title}
            loading="lazy"
            decoding="async"
            onError={() => setImgFailed(true)}
            className="recipe-thumb-img"
          />
        )}
        {showFallback && (
          <div className="ph">
            {recipe.title.split(" ").slice(0, 3).join(" ")}
          </div>
        )}
        <span className="source">{sourceDomain}</span>
      </div>
      <div className="recipe-body">
        <div className="recipe-title">
          {loading ? "Extracting..." : recipe.title}
        </div>
      </div>
    </div>
  );
}
