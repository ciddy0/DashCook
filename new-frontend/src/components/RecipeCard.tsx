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
  const sourceDomain = (() => {
    try {
      return new URL(recipe.source_url).hostname.replace(/^www\./, "");
    } catch {
      return recipe.source_url;
    }
  })();

  return (
    <div
      className="recipe-thumb"
      style={
        recipe.image_url
          ? {
              backgroundImage: `url(${recipe.image_url})`,
              backgroundSize: "cover",
              backgroundPosition: "center",
            }
          : { background: "var(--surface-2, #C39267)" }
      }
    >
      {!recipe.image_url && (
        <div className="ph">
          {recipe.title.split(" ").slice(0, 3).join(" ")}
        </div>
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
    <div className="recipe-card" onClick={() => onOpen(recipe.id)}>
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
