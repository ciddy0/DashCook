import { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { Icon } from "../components/Icon";
import { SouschatLogoIcon } from "../components/SouschatLogoIcon";
import { getRecipe } from "../store";
import { ingredientLine } from "../helpers";

function parseServings(s: string | null): number {
  if (!s) return 4;
  const n = parseInt(s, 10);
  return isNaN(n) ? 4 : n;
}

export function CookNow() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const recipe = getRecipe(id ?? "");
  const baseServings = parseServings(recipe?.servings ?? null);
  const servings = Number(searchParams.get("servings")) || baseServings;

  const [idx, setIdx] = useState(0);

  const recipeId = recipe?.id;
  const instructionCount = recipe?.instructions.length ?? 0;

  // keyboard nav
  useEffect(() => {
    const lastStep = instructionCount - 1;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") setIdx((i) => Math.min(lastStep, i + 1));
      else if (e.key === "ArrowLeft") setIdx((i) => Math.max(0, i - 1));
      else if (e.key === "Escape") navigate(recipeId ? `/recipe/${recipeId}` : "/");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [instructionCount, recipeId, navigate]);

  if (!recipe) {
    return (
      <div className="page" style={{ textAlign: "center", paddingTop: 80 }}>
        <h2>Recipe not found</h2>
        <button className="btn" onClick={() => navigate("/")}>
          Go Home
        </button>
      </div>
    );
  }

  const scale = servings / baseServings;
  const step = recipe.instructions[idx];
  const lastIdx = recipe.instructions.length - 1;
  const progress = ((idx + 1) / recipe.instructions.length) * 100;

  const onExit = () => navigate(`/recipe/${recipe.id}`);

  // ingredients used in this step
  const stepIngredients =
    idx === 0
      ? recipe.ingredients.slice(
          0,
          Math.min(4, recipe.ingredients.length)
        )
      : [];

  return (
    <div className="cook-overlay" role="dialog" aria-modal="true" aria-label="Cook Now">
      {/* Header */}
      <header className="cook-header">
        <SouschatLogoIcon className="logo-mark" style={{ width: 36, height: 36 }} />
        <div className="cook-title">
          Cooking <b>{recipe.title}</b>
        </div>
        <span className="stat">
          <Icon name="users" size={14} />
          {servings} servings
        </span>
        <button
          className="icon-btn"
          onClick={onExit}
          aria-label="Exit cook mode"
        >
          <Icon name="x" size={18} />
        </button>
      </header>

      {/* Body */}
      <div className="cook-body">
        <div className="cook-step-card">
          <div className="cook-step-num">
            <span>
              Step {idx + 1} of {recipe.instructions.length}
            </span>
            <div style={{ display: "flex", gap: 6 }}>
              {recipe.instructions.map((_, i) => (
                <span
                  key={i}
                  className={
                    "pip " +
                    (i === idx ? "active" : i < idx ? "done" : "")
                  }
                  style={{ transition: "all var(--t-med)" }}
                />
              ))}
            </div>
          </div>

          <div className="cook-step-text">{step}</div>

          {stepIngredients.length > 0 && (
            <div className="cook-ing-list">
              <div className="lbl">You'll need</div>
              {stepIngredients.map((ing, i) => {
                const line = ingredientLine(ing, scale);
                return (
                  <div key={i} className="ing">
                    {line.qty && (
                      <span className="qty">{line.qty} </span>
                    )}
                    {line.item}
                  </div>
                );
              })}
              {recipe.ingredients.length > stepIngredients.length && (
                <div
                  style={{
                    fontSize: 13,
                    color: "var(--text-3)",
                    fontWeight: 500,
                    marginTop: 4,
                  }}
                >
                  + {recipe.ingredients.length - stepIngredients.length}{" "}
                  more — check the Ingredients tab anytime.
                </div>
              )}
            </div>
          )}

          {idx === lastIdx && (
            <div className="banner banner-success">
              <div>
                <b>Last step — you've got this!</b>
                <div style={{ fontSize: 15, fontWeight: 500 }}>
                  Tap "Finish" when you're done plating.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="cook-footer">
        <button
          className="btn btn-secondary"
          onClick={() => setIdx((i) => Math.max(0, i - 1))}
          disabled={idx === 0}
        >
          <Icon name="arrow-l" size={16} /> Back
        </button>

        <div
          className="progress-track"
          role="progressbar"
          aria-valuemin={1}
          aria-valuemax={recipe.instructions.length}
          aria-valuenow={idx + 1}
          aria-label={`Step ${idx + 1} of ${recipe.instructions.length}`}
        >
          <div
            className="progress-fill"
            style={{
              width: `${progress}%`,
              background: "var(--success)",
            }}
          />
        </div>

        {idx < lastIdx ? (
          <button
            className="btn btn-success"
            onClick={() => setIdx((i) => i + 1)}
          >
            Next <Icon name="arrow-r" size={16} />
          </button>
        ) : (
          <button className="btn btn-success" onClick={onExit}>
            <Icon name="check" size={16} /> Finish
          </button>
        )}
      </footer>
    </div>
  );
}
