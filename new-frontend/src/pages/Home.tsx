import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "../components/Icon";
import { RecipeCard } from "../components/RecipeCard";
import { ExplorePantry } from "../components/ExplorePantry";
import { extractRecipe } from "../api";
import { getRecipes, addRecipe } from "../store";
import { EXAMPLE_RECIPE_URL } from "../data/browseRecipes";
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

  const submit = async (e?: React.SyntheticEvent) => {
    e?.preventDefault();
    // Empty input? Extract the example recipe from the placeholder.
    const target = url.trim() || EXAMPLE_RECIPE_URL;
    if (!/^https?:\/\//.test(target) && !target.includes(".")) {
      setError(
        "That doesn't look like a link — try pasting the whole URL."
      );
      return;
    }
    setError("");
    setPasting(true);
    try {
      const recipe = await extractRecipe(target);
      addRecipe(recipe);
      setUrl("");
      navigate(`/recipe/${recipe.id}`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong. Please try again."
      );
    } finally {
      setPasting(false);
    }
  };

  const recent = getRecipes().slice(0, 4);
  const savedRecipes: Recipe[] = getRecipes().filter((r) => saved[r.id]);

  return (
    <div className="page">
      {/* Hero */}
      <section className="hero" style={{ marginBottom: 56 }}>
        <h1>
          Paste a recipe. Get the <span className="hl">recipe</span>.
        </h1>
        <p className="sub">
          souschat strips the ads, the life stories, and the SEO fluff, and
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
            placeholder={EXAMPLE_RECIPE_URL}
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
          style={{
            marginTop: 24,
            textAlign: "center",
          }}
        >
          <span
            className="tag tag-soft"
            style={{ fontSize: 11, letterSpacing: 1 }}
          >
            Works with most recipe sites
          </span>
          <p style={{ marginTop: 10, fontSize: 13, fontWeight: 500 }}>
            Not sure? Just hit Extract to try the example above.
          </p>
        </div>
      </section>

      {/* Explore the pantry — browse what's already in the database */}
      <ExplorePantry />

      {/* Recently extracted */}
      {recent.length > 0 && (
        <section style={{ marginBottom: 56 }}>
          <div className="section-header">
            <h2>Recently extracted</h2>
            <span className="eyebrow">{recent.length} recipes</span>
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
      )}

      {/* Saved */}
      <section>
        <div className="section-header">
          <h2>Your saved recipes</h2>
          <span className="eyebrow">{savedRecipes.length} saved</span>
        </div>

        {savedRecipes.length === 0 ? (
          <div className="card empty-state">
            <h3>No saved recipes yet. let's fix that :3</h3>
            <p>
              Tap the bookmark on any recipe to keep it. We'll remember the
              servings you cooked with last time.
            </p>
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
