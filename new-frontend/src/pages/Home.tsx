import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "../components/Icon";
import { RecipeCard } from "../components/RecipeCard";
import { RECIPES } from "../data/recipes";
import type { Recipe } from "../types";

export function Home({
  saved,
  onToggleSave,
}: {
  saved: Record<string, boolean>;
  onToggleSave: (id: string) => void;
}) {
  const [url, setUrl] = useState("");
  const [pasting, setPasting] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const onOpen = (id: string) => navigate(`/recipe/${id}`);

  const submit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!url.trim()) {
      setError("Paste a recipe link first :)");
      return;
    }
    if (!/^https?:\/\//.test(url) && !url.includes(".")) {
      setError(
        "That doesn't look like a link — try pasting the whole URL."
      );
      return;
    }
    setError("");
    setPasting(true);
    setTimeout(() => {
      setPasting(false);
      const r = RECIPES[Math.floor(Math.random() * RECIPES.length)];
      navigate(`/recipe/${r.id}`);
      setUrl("");
    }, 1100);
  };

  const recent = RECIPES.slice(0, 3);
  const savedRecipes: Recipe[] = RECIPES.filter((r) => saved[r.id]);

  return (
    <div className="page">
      {/* Hero */}
      <section className="hero" style={{ marginBottom: 56 }}>
        <h1>
          Paste a recipe. Get the <span className="hl">recipe</span>.
        </h1>
        <p className="sub">
          souschat strips the ads, the life stories, and the SEO fluff — and
          gives you a calm, cookable recipe you can actually use in the
          kitchen.
        </p>

        <form className="paster" onSubmit={submit}>
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              paddingLeft: 10,
              color: "var(--text-3)",
            }}
          >
            <Icon name="link" size={18} />
          </span>
          <input
            className="input"
            placeholder="https://example.com/best-tomato-pasta-ever..."
            value={url}
            onChange={(e) => {
              setUrl(e.target.value);
              setError("");
            }}
            disabled={pasting}
            aria-label="Recipe URL"
          />
          <button className="btn" type="submit" disabled={pasting}>
            {pasting ? "Stripping the fluff..." : "Extract"}
          </button>
        </form>

        {error && (
          <div
            style={{
              marginTop: 14,
              color: "var(--error)",
              fontWeight: 600,
              fontSize: 14,
            }}
          >
            {error}
          </div>
        )}

        <div
          className="row"
          style={{
            justifyContent: "center",
            gap: 18,
            marginTop: 24,
            color: "var(--text-3)",
            fontSize: 13,
            fontWeight: 600,
            letterSpacing: 0.4,
            textTransform: "uppercase",
          }}
        >
          <span>Works with</span>
          <span style={{ color: "var(--text-2)" }}>&middot; any blog</span>
          <span style={{ color: "var(--text-2)" }}>
            &middot; NYT Cooking
          </span>
          <span style={{ color: "var(--text-2)" }}>
            &middot; Serious Eats
          </span>
          <span style={{ color: "var(--text-2)" }}>&middot; Food52</span>
        </div>
      </section>

      {/* Recently extracted */}
      <section style={{ marginBottom: 56 }}>
        <div className="section-header">
          <h2>Recently extracted</h2>
          <span className="eyebrow">Last 7 days</span>
        </div>
        <div className="recipe-grid">
          {recent.map((r) => (
            <RecipeCard
              key={r.id}
              recipe={r}
              saved={!!saved[r.id]}
              onToggleSave={onToggleSave}
              onOpen={onOpen}
            />
          ))}
        </div>
      </section>

      {/* Saved */}
      <section>
        <div className="section-header">
          <h2>Your saved recipes</h2>
          <span className="eyebrow">{savedRecipes.length} saved</span>
        </div>

        {savedRecipes.length === 0 ? (
          <div
            className="card"
            style={{ textAlign: "center", padding: "44px 24px" }}
          >
            <div style={{ fontSize: 40, marginBottom: 8 }}>&#x1F431;</div>
            <h3
              style={{
                fontSize: 20,
                fontWeight: 600,
                marginBottom: 6,
              }}
            >
              No saved recipes yet — let's fix that.
            </h3>
            <p
              style={{
                color: "var(--text-2)",
                fontWeight: 500,
                fontSize: 15,
                maxWidth: 420,
                margin: "0 auto 18px",
              }}
            >
              Tap the bookmark on any recipe to keep it. We'll remember the
              servings you cooked with last time.
            </p>
            <button
              className="btn btn-accent"
              onClick={() => onToggleSave(RECIPES[0].id)}
            >
              Save one to try
            </button>
          </div>
        ) : (
          <div className="recipe-grid">
            {savedRecipes.map((r) => (
              <RecipeCard
                key={r.id}
                recipe={r}
                saved
                onToggleSave={onToggleSave}
                onOpen={onOpen}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
