import type { BrowseRecipe, Recipe, SimilarRecipe } from "./types";
import { DUMMY_DB_RECIPES } from "./data/browseRecipes";

const API_BASE =
  "https://dashcook-api.happygrass-bd874e33.westus3.azurecontainerapps.io";
const API_URL = `${API_BASE}/url`;

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

export async function extractRecipe(url: string): Promise<Recipe> {
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  if (!res.ok) {
    if (res.status === 422) {
      throw new Error("Couldn't extract a recipe from that URL. Try a different link.");
    }
    throw new Error("Something went wrong. Please try again.");
  }

  const data = await res.json();

  return {
    id: slugify(data.title || "recipe"),
    title: data.title ?? "Untitled Recipe",
    source_url: data.source_url ?? url,
    image_url: data.image_url ?? null,
    prep_time: data.prep_time ?? null,
    cook_time: data.cook_time ?? null,
    total_time: data.total_time ?? null,
    servings: data.servings ?? null,
    ingredients: (data.ingredients ?? []).map((ing: any) => ({
      raw: ing.raw ?? "",
      name: ing.name ?? "",
      quantity: ing.quantity ?? null,
      quantity_max: ing.quantity_max ?? null,
      unit: ing.unit ?? null,
      scalable: ing.scalable ?? true,
    })),
    instructions: data.instructions ?? [],
  };
}

// TODO: swap for the real backend route once GET /recipes + clustering land.
// Expected contract: GET `${API_BASE}/recipes` ->
//   [{ title, source_url, image_url, category, distance? }]
export async function fetchDbRecipes(): Promise<BrowseRecipe[]> {
  await new Promise((r) => setTimeout(r, 400)); // simulate network
  return DUMMY_DB_RECIPES;
}

export async function searchRecipes(
  query: string,
  limit = 6,
): Promise<SimilarRecipe[]> {
  try {
    const params = new URLSearchParams({ q: query, limit: String(limit) });
    const res = await fetch(`${API_BASE}/search?${params}`);
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function fetchSimilarRecipes(
  sourceUrl: string,
  limit = 6,
): Promise<SimilarRecipe[]> {
  try {
    const params = new URLSearchParams({ url: sourceUrl, limit: String(limit) });
    const res = await fetch(`${API_BASE}/similar?${params}`);
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}
