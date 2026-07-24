import { useState } from "react";
import { Icon } from "./Icon";
import type { Recipe } from "../types";

function RecipeThumb({
  recipe,
  saved,
  onToggleSave,
}: {
  recipe: Recipe;
  saved: boolean;
  onToggleSave: (id: string) => void;
}) {
  const [imgFailed, setImgFailed] = useState(false);
  const showFallback = !recipe.image_url || imgFailed;

  const sourceDomain = (() => {
    try {
      return new URL(recipe.source_url).hostname.replace(/^www\./, "");
    } catch {
      return recipe.source_url;
    }
  })();

  return (
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
      <button
        className={"save" + (saved ? " saved" : "")}
        onClick={(e) => {
          e.stopPropagation();
          onToggleSave(recipe.id);
        }}
        title={saved ? "Saved" : "Save"}
        aria-label={saved ? "Unsave recipe" : "Save recipe"}
      >
        <Icon name={saved ? "bookmark-fill" : "bookmark"} size={18} />
      </button>
    </div>
  );
}

export function RecipeCard({
  recipe,
  saved,
  onToggleSave,
  onOpen,
}: {
  recipe: Recipe;
  saved: boolean;
  onToggleSave: (id: string) => void;
  onOpen: (id: string) => void;
}) {
  const timeDisplay = recipe.total_time || recipe.cook_time || recipe.prep_time;
  const servings = recipe.servings ? parseInt(recipe.servings, 10) : null;

  return (
    <div className="recipe-card">
      {/* Stretched button covers the card so the whole surface opens the recipe,
          while the save button stays a real sibling (not nested in a button). */}
      <button
        className="recipe-card-open"
        aria-label={`View ${recipe.title}`}
        onClick={() => onOpen(recipe.id)}
      />
      <RecipeThumb
        recipe={recipe}
        saved={saved}
        onToggleSave={onToggleSave}
      />
      <div className="recipe-body">
        <div className="recipe-title">{recipe.title}</div>
        <div className="recipe-meta">
          {timeDisplay && (
            <span>
              <Icon name="clock" size={14} /> {timeDisplay}
            </span>
          )}
          {servings && (
            <span>
              <Icon name="users" size={14} /> Serves {servings}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
