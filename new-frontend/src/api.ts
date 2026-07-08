import type {
  Category,
  Ingredient,
  Recipe,
  RecipeListResponse,
  SimilarRecipe,
} from "./types";

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

export interface TicketInput {
  subject: string;
  description: string;
  recipe_url?: string | null;
}

export async function submitTicket(input: TicketInput): Promise<void> {
  const res = await fetch(`${API_BASE}/tickets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      category: "parser",
      subject: input.subject,
      description: input.description,
      ...(input.recipe_url ? { recipe_url: input.recipe_url } : {}),
    }),
  });

  if (!res.ok) {
    if (res.status === 429) {
      throw new Error(
        "Too many reports have been submitted recently. Please try again later.",
      );
    }
    if (res.status === 422) {
      throw new Error("Please check the form and try again.");
    }
    throw new Error("Couldn't submit your report. Please try again.");
  }
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

export async function listCategories(): Promise<Category[]> {
  try {
    const res = await fetch(`${API_BASE}/categories`);
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
    const params = new URLSearchParams();
    if (opts.limit != null) params.set("limit", String(opts.limit));
    if (opts.cursor) params.set("cursor", opts.cursor);
    if (opts.category != null) params.set("category", String(opts.category));
    const res = await fetch(`${API_BASE}/recipes?${params}`);
    if (!res.ok) return { items: [], next_cursor: null };
    return await res.json();
  } catch {
    return { items: [], next_cursor: null };
  }
}
