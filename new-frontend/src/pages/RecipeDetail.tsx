import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Icon } from "../components/Icon";
import { RECIPES } from "../data/recipes";
import { ingredientLine } from "../helpers";

export function RecipeDetail({
  saved,
  onToggleSave,
}: {
  saved: Record<string, boolean>;
  onToggleSave: (id: string) => void;
}) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const recipe = RECIPES.find((r) => r.id === id);

  const [servings, setServings] = useState(recipe?.servings ?? 4);
  const [checked, setChecked] = useState<Record<number, boolean>>({});

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

  const scale = servings / recipe.servings;
  const adjusted = servings !== recipe.servings;
  const toggleCheck = (i: number) =>
    setChecked((s) => ({ ...s, [i]: !s[i] }));
  const checkedCount = Object.values(checked).filter(Boolean).length;
  const allChecked = checkedCount === recipe.ingredients.length;
  const isSaved = !!saved[recipe.id];

  return (
    <div className="page">
      <div className="row print-hide" style={{ marginBottom: 18 }}>
        <button
          className="btn-ghost btn btn-sm"
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
          onClick={() => window.print()}
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
        <div
          className="recipe-thumb"
          style={{
            background: recipe.color,
            borderRadius: "var(--r-xl)",
            border: "2px solid var(--border)",
            aspectRatio: "5/4",
            minHeight: 280,
          }}
        >
          <div className="ph">{recipe.title}</div>
          <span className="source">{recipe.source}</span>
        </div>
        <div className="col" style={{ justifyContent: "center", gap: 16 }}>
          <span className="tag tag-soft" style={{ alignSelf: "flex-start" }}>
            <Icon name="sparkle" size={12} /> Recipe
          </span>
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
          <p
            style={{
              color: "var(--text-2)",
              fontSize: 17,
              lineHeight: 1.5,
              textWrap: "pretty",
              maxWidth: 460,
            }}
          >
            {recipe.summary}
          </p>
          <div
            className="row"
            style={{ flexWrap: "wrap", gap: 10, marginTop: 6 }}
          >
            <span className="stat">
              <Icon name="clock" size={16} />
              {recipe.timeMin} min
            </span>
            <span className="stat">
              <Icon name="users" size={16} />
              {servings} servings
            </span>
            <span className="stat">
              <Icon name="sparkle" size={16} />
              {recipe.difficulty}
            </span>
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
              onClick={() => window.print()}
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
                  ? `Originally ${recipe.servings}`
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
              <span className="em" style={{ fontSize: 18 }}>
                &#x2728;
              </span>
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
            <span className="eyebrow">{recipe.steps.length} steps</span>
          </div>
          <div className="col" style={{ gap: 14 }}>
            {recipe.steps.map((step, i) => (
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

      <style>{`
        @media (max-width: 820px) {
          .recipe-header-grid { grid-template-columns: 1fr !important; }
          .recipe-body-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}
