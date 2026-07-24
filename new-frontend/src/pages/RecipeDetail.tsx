import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Icon } from "../components/Icon";
import { ReportIssueModal } from "../components/ReportIssueModal";
import { SimilarRecipeCard } from "../components/SimilarRecipeCard";
import { RecipeGridSkeleton } from "../components/RecipeGridSkeleton";
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
  const [reportOpen, setReportOpen] = useState(false);

  const sourceUrl = recipe?.source_url;
  useEffect(() => {
    if (!sourceUrl) return;
    let active = true;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- show the loading state while the fetch is in flight
    setSimilarLoading(true);
    fetchSimilarRecipes(sourceUrl).then((results) => {
      if (!active) return;
      setSimilarRecipes(results);
      setSimilarLoading(false);
    });
    return () => {
      active = false;
    };
  }, [sourceUrl]);

  if (!recipe) {
    return (
      <div className="page" style={{ textAlign: "center", paddingTop: "var(--s-20)" }}>
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
      <div className="row print-hide" style={{ marginBottom: "var(--s-5)" }}>
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
        <button
          className="icon-btn"
          onClick={() => setReportOpen(true)}
          title="Report issue"
          aria-label="Report an issue"
        >
          <Icon name="flag" size={18} />
        </button>
      </div>

      {reportOpen && (
        <ReportIssueModal
          recipeUrl={recipe.source_url}
          onClose={() => setReportOpen(false)}
        />
      )}

      {/* Header */}
      <div
        className="recipe-header-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "1.05fr 1fr",
          gap: "clamp(16px, 4vw, 32px)",
          alignItems: "stretch",
          marginBottom: "var(--s-10)",
        }}
      >
        {recipe.image_url && !imgFailed ? (
          <div
            style={{
              borderRadius: "var(--r-xl)",
              border: "2px solid var(--border)",
              overflow: "hidden",
              aspectRatio: "5/4",
              minHeight: "clamp(200px, 40vw, 280px)",
            }}
          >
            <img
              src={recipe.image_url}
              alt={recipe.title}
              width={500}
              height={400}
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
              minHeight: "clamp(200px, 40vw, 280px)",
            }}
          >
            <span className="source">{sourceDomain}</span>
          </div>
        )}
        <div className="col" style={{ justifyContent: "center", gap: "var(--s-4)" }}>
          <h1
            style={{
              fontSize: "clamp(28px, 5vw, 40px)",
              fontWeight: 700,
              lineHeight: 1.05,
              letterSpacing: -0.8,
              textWrap: "balance",
              overflowWrap: "anywhere",
            }}
          >
            {recipe.title}
          </h1>
          <div
            className="row"
            style={{ flexWrap: "wrap", gap: "var(--s-3)", marginTop: "var(--s-2)" }}
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
              fontSize: "var(--fs-sm)",
              color: "var(--text-3)",
              fontWeight: 500,
            }}
          >
            From{" "}
            <a
              href={recipe.source_url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                color: "var(--text-2)",
                textDecoration: "underline",
                overflowWrap: "anywhere",
              }}
            >
              {sourceDomain}
            </a>
          </div>
          <div
            className="row print-hide"
            style={{ gap: "var(--s-3)", marginTop: "var(--s-3)" }}
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
          gap: "clamp(16px, 4vw, 32px)",
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
              padding: "var(--s-4)",
              marginBottom: "var(--s-4)",
              display: "flex",
              alignItems: "center",
              gap: "var(--s-4)",
            }}
          >
            <div style={{ flex: 1 }}>
              <div
                style={{
                  fontSize: "var(--fs-xs)",
                  fontWeight: 700,
                  letterSpacing: 1.2,
                  textTransform: "uppercase",
                  color: "var(--text-3)",
                  marginBottom: "var(--s-1)",
                }}
              >
                Servings
              </div>
              <div
                style={{
                  fontSize: "var(--fs-sm)",
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
              style={{ marginBottom: "var(--s-4)", padding: "var(--s-3) var(--s-4)" }}
            >
              <div style={{ fontSize: "var(--fs-sm)", fontWeight: 600 }}>
                Scaled to {servings} — ingredient amounts updated below.
              </div>
            </div>
          )}

          <div className="col" style={{ gap: "var(--s-2)" }}>
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
              style={{ marginTop: "var(--s-4)" }}
            >
              <div>
                <b>Nicely done!</b>
                <div style={{ fontSize: "var(--fs-sm)", fontWeight: 500 }}>
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
          <div className="col" style={{ gap: "var(--s-4)" }}>
            {recipe.instructions.map((step, i) => (
              <div
                key={i}
                className="card"
                style={{
                  display: "flex",
                  gap: "var(--s-5)",
                  alignItems: "flex-start",
                  padding: "var(--s-5)",
                }}
              >
                <span
                  className="bubble"
                  style={{ width: "var(--touch)", height: "var(--touch)", fontSize: "var(--fs-lg)" }}
                >
                  {i + 1}
                </span>
                <div
                  style={{
                    paddingTop: "var(--s-2)",
                    fontSize: "var(--fs-md)",
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
        <section className="print-hide" style={{ marginTop: "var(--s-12)" }}>
          <div className="section-header">
            <h2>Similar Recipes</h2>
          </div>
          <RecipeGridSkeleton count={6} />
        </section>
      )}

      {!similarLoading && similarRecipes.length > 0 && (
        <section className="print-hide" style={{ marginTop: "var(--s-12)" }}>
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
