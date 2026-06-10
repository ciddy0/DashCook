import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Icon } from "../components/Icon";
import { SimilarRecipeCard } from "../components/SimilarRecipeCard";
import { getRecipe } from "../store";
import { fetchSimilarRecipes } from "../api";
import { ingredientLine } from "../helpers";
import type { SimilarRecipe } from "../types";

function parseServings(s: string | null): number {
  if (!s) return 4;
  const n = parseInt(s, 10);
  return isNaN(n) ? 4 : n;
}

export function RecipeDetail({
  saved,
  onToggleSave,
}: {
  saved: Record<string, boolean>;
  onToggleSave: (id: string) => void;
}) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const recipe = getRecipe(id ?? "");

  const baseServings = parseServings(recipe?.servings ?? null);
  const [servings, setServings] = useState(baseServings);
  const [checked, setChecked] = useState<Record<number, boolean>>({});
  const [similarRecipes, setSimilarRecipes] = useState<SimilarRecipe[]>([]);
  const [similarLoading, setSimilarLoading] = useState(false);
  const [imgFailed, setImgFailed] = useState(false);

  useEffect(() => {
    if (!recipe) return;
    setSimilarLoading(true);
    fetchSimilarRecipes(recipe.source_url).then((results) => {
      setSimilarRecipes(results);
      setSimilarLoading(false);
    });
  }, [recipe?.source_url]);

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
  const adjusted = servings !== baseServings;
  const toggleCheck = (i: number) =>
    setChecked((s) => ({ ...s, [i]: !s[i] }));
  const checkedCount = Object.values(checked).filter(Boolean).length;
  const allChecked = checkedCount === recipe.ingredients.length;
  const isSaved = !!saved[recipe.id];

  const timeDisplay = recipe.total_time || recipe.cook_time || recipe.prep_time;
  const sourceDomain = (() => {
    try {
      return new URL(recipe.source_url).hostname.replace(/^www\./, "");
    } catch {
      return recipe.source_url;
    }
  })();

  return (
    <div className="page">
      <div className="row print-hide" style={{ marginBottom: 18 }}>
        <button
          className="btn btn-secondary"
          onClick={() => navigate("/")}
        >
          <Icon name="arrow-l" size={16} /> Back
        </button>
        <div className="spacer" />
        <button
          className={"icon-btn" + (isSaved ? " is-active" : "")}
          onClick={() => onToggleSave(recipe.id)}
          title={isSaved ? "Saved" : "Save"}
          aria-label={isSaved ? "Unsave" : "Save"}
        >
          <Icon name={isSaved ? "bookmark-fill" : "bookmark"} size={18} />
        </button>
        <button
          className="icon-btn"
          onClick={() => setTimeout(() => window.print(), 150)}
          title="Print"
          aria-label="Print"
        >
          <Icon name="print" size={18} />
        </button>
      </div>

      {/* Header */}
      <div
        className="recipe-header-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "1.05fr 1fr",
          gap: 32,
          alignItems: "stretch",
          marginBottom: 40,
        }}
      >
        {recipe.image_url && !imgFailed ? (
          <div
            style={{
              borderRadius: "var(--r-xl)",
              border: "2px solid var(--border)",
              overflow: "hidden",
              aspectRatio: "5/4",
              minHeight: 280,
            }}
          >
            <img
              src={recipe.image_url}
              alt={recipe.title}
              fetchPriority="high"
              decoding="async"
              onError={() => setImgFailed(true)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                display: "block",
              }}
            />
          </div>
        ) : (
          <div
            className="recipe-thumb recipe-thumb-fallback"
            style={{
              borderRadius: "var(--r-xl)",
              border: "2px solid var(--border)",
              aspectRatio: "5/4",
              minHeight: 280,
            }}
          >
            <div className="ph">{recipe.title}</div>
            <span className="source">{sourceDomain}</span>
          </div>
        )}
        <div className="col" style={{ justifyContent: "center", gap: 16 }}>
          <h1
            style={{
              fontSize: 40,
              fontWeight: 700,
              lineHeight: 1.05,
              letterSpacing: -0.8,
              textWrap: "balance",
            }}
          >
            {recipe.title}
          </h1>
          <div
            className="row"
            style={{ flexWrap: "wrap", gap: 10, marginTop: 6 }}
          >
            {timeDisplay && (
              <span className="stat">
                <Icon name="clock" size={16} />
                {timeDisplay}
              </span>
            )}
            <span className="stat">
              <Icon name="users" size={16} />
              {servings} servings
            </span>
          </div>
          <div
            style={{
              fontSize: 13,
              color: "var(--text-3)",
              fontWeight: 500,
            }}
          >
            From{" "}
            <a
              href={recipe.source_url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "var(--text-2)", textDecoration: "underline" }}
            >
              {sourceDomain}
            </a>
          </div>
          <div
            className="row print-hide"
            style={{ gap: 12, marginTop: 12 }}
          >
            <button
              className="btn btn-xl btn-success"
              onClick={() => navigate(`/cook/${recipe.id}?servings=${servings}`)}
            >
              <Icon name="play" size={18} /> Cook Now
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => setTimeout(() => window.print(), 150)}
            >
              <Icon name="print" size={16} /> Print
            </button>
          </div>
        </div>
      </div>

      <div
        className="recipe-body-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 0.95fr) minmax(0, 1.4fr)",
          gap: 32,
        }}
      >
        {/* Ingredients */}
        <aside>
          <div className="section-header">
            <h2>Ingredients</h2>
            <span className="eyebrow">
              {checkedCount}/{recipe.ingredients.length}
            </span>
          </div>

          {/* Servings adjuster */}
          <div
            className="card print-hide"
            style={{
              padding: 16,
              marginBottom: 16,
              display: "flex",
              alignItems: "center",
              gap: 14,
            }}
          >
            <div style={{ flex: 1 }}>
              <div
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  letterSpacing: 1.2,
                  textTransform: "uppercase",
                  color: "var(--text-3)",
                  marginBottom: 4,
                }}
              >
                Servings
              </div>
              <div
                style={{
                  fontSize: 14,
                  color: "var(--text-2)",
                  fontWeight: 500,
                }}
              >
                {adjusted
                  ? `Originally ${baseServings}`
                  : "Scale up or down"}
              </div>
            </div>
            <div className="stepper">
              <button
                onClick={() => setServings((s) => Math.max(1, s - 1))}
                disabled={servings <= 1}
                aria-label="Fewer"
              >
                &minus;
              </button>
              <span className="val">{servings}</span>
              <button
                onClick={() => setServings((s) => Math.min(24, s + 1))}
                disabled={servings >= 24}
                aria-label="More"
              >
                +
              </button>
            </div>
          </div>

          {adjusted && (
            <div
              className="banner banner-info"
              style={{ marginBottom: 16, padding: "10px 14px" }}
            >
              <div style={{ fontSize: 13, fontWeight: 600 }}>
                Scaled to {servings} — ingredient amounts updated below.
              </div>
            </div>
          )}

          <div className="col" style={{ gap: 8 }}>
            {recipe.ingredients.map((ing, i) => {
              const line = ingredientLine(ing, scale);
              return (
                <div
                  key={i}
                  className={
                    "checkbox-row" + (checked[i] ? " checked" : "")
                  }
                  onClick={() => toggleCheck(i)}
                  role="checkbox"
                  aria-checked={!!checked[i]}
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === " " || e.key === "Enter") {
                      e.preventDefault();
                      toggleCheck(i);
                    }
                  }}
                >
                  <span className="check-box">
                    {checked[i] ? "\u2713" : ""}
                  </span>
                  <span className="check-label">
                    {line.qty && (
                      <span className="qty">{line.qty} </span>
                    )}
                    {line.item}
                  </span>
                </div>
              );
            })}
          </div>

          {allChecked && (
            <div
              className="banner banner-success"
              style={{ marginTop: 16 }}
            >
              <span className="em">&#x1F389;</span>
              <div>
                <b>Nicely done!</b>
                <div style={{ fontSize: 14, fontWeight: 500 }}>
                  Everything's prepped. Tap Cook Now whenever you're ready.
                </div>
              </div>
            </div>
          )}
        </aside>

        {/* Steps */}
        <section>
          <div className="section-header">
            <h2>Steps</h2>
            <span className="eyebrow">{recipe.instructions.length} steps</span>
          </div>
          <div className="col" style={{ gap: 14 }}>
            {recipe.instructions.map((step, i) => (
              <div
                key={i}
                className="card"
                style={{
                  display: "flex",
                  gap: 18,
                  alignItems: "flex-start",
                  padding: 20,
                }}
              >
                <span
                  className="bubble"
                  style={{ width: 44, height: 44, fontSize: 18 }}
                >
                  {i + 1}
                </span>
                <div
                  style={{
                    paddingTop: 6,
                    fontSize: 16,
                    lineHeight: 1.55,
                    color: "var(--text)",
                    fontWeight: 500,
                    textWrap: "pretty",
                  }}
                >
                  {step}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {similarLoading && (
        <section className="print-hide" style={{ marginTop: 48 }}>
          <div className="section-header">
            <h2>Similar Recipes</h2>
          </div>
          <div className="recipe-grid">
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="skeleton-card">
                <div className="skeleton-thumb skeleton" />
                <div className="skeleton-body">
                  <div className="skeleton-line skeleton" style={{ width: "85%" }} />
                  <div className="skeleton-line skeleton skeleton-line-short" />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {!similarLoading && similarRecipes.length > 0 && (
        <section className="print-hide" style={{ marginTop: 48 }}>
          <div className="section-header">
            <h2>Similar Recipes</h2>
          </div>
          <div className="recipe-grid">
            {similarRecipes.map((sr) => (
              <SimilarRecipeCard key={sr.source_url} recipe={sr} />
            ))}
          </div>
        </section>
      )}

      <style>{`
        @media (max-width: 820px) {
          .recipe-header-grid { grid-template-columns: 1fr !important; }
          .recipe-body-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}
