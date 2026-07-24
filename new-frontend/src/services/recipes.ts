import type {
  Category,
  DiscoverResult,
  Ingredient,
  Recipe,
  RecipeListResponse,
  SimilarRecipe,
} from "../types";
import { apiUrl, postJson } from "./client";

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

export async function extractRecipe(url: string): Promise<Recipe> {
  const res = await postJson("/url", { url });

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
    ingredients: (data.ingredients ?? []).map((ing: Partial<Ingredient>) => ({
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

export async function discoverRecipes(
  query: string,
  limit = 5,
): Promise<DiscoverResult> {
  const empty: DiscoverResult = {
    mode: "search",
    answer: null,
    recipes: [],
    remaining: 0,
  };
  try {
    const res = await postJson("/discover", { query, limit });
    if (!res.ok) return empty;
    return await res.json();
  } catch {
    return empty;
  }
}

export async function fetchSimilarRecipes(
  sourceUrl: string,
  limit = 6,
): Promise<SimilarRecipe[]> {
  try {
    const res = await fetch(apiUrl("/similar", { url: sourceUrl, limit }));
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function listCategories(): Promise<Category[]> {
  try {
    const res = await fetch(apiUrl("/categories"));
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function listRecipes(opts: {
  limit?: number;
  cursor?: string | null;
  category?: number;
} = {}): Promise<RecipeListResponse> {
  try {
    const res = await fetch(
      apiUrl("/recipes", {
        limit: opts.limit,
        cursor: opts.cursor,
        category: opts.category,
      }),
    );
    if (!res.ok) return { items: [], next_cursor: null };
    return await res.json();
  } catch {
    return { items: [], next_cursor: null };
  }
}
