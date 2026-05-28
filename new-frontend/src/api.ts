import type { Recipe } from "./types";

const API_URL =
  "https://dashcook-api.happygrass-bd874e33.westus3.azurecontainerapps.io/url";

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
