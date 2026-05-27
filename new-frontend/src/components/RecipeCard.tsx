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
  return (
    <div className="recipe-thumb" style={{ background: recipe.color }}>
      <div className="ph">
        {recipe.title.split(" ").slice(0, 3).join(" ")}
      </div>
      <span className="source">{recipe.source}</span>
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
          <span>
            <Icon name="clock" size={14} /> {recipe.timeMin} min
          </span>
          <span>
            <Icon name="users" size={14} /> Serves {recipe.servings}
          </span>
          <span>
            <Icon name="sparkle" size={14} /> {recipe.difficulty}
          </span>
        </div>
      </div>
    </div>
  );
}
