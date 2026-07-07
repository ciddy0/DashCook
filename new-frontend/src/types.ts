export interface Ingredient {
  raw: string;
  name: string;
  quantity: number | null;
  quantity_max: number | null;
  unit: string | null;
  scalable: boolean;
}

export interface Recipe {
  id: string;
  title: string;
  source_url: string;
  image_url: string | null;
  prep_time: string | null;
  cook_time: string | null;
  total_time: string | null;
  servings: string | null;
  ingredients: Ingredient[];
  instructions: string[];
}

export interface SimilarRecipe {
  title: string;
  source_url: string;
  image_url: string | null;
  distance: number;
}

export interface Category {
  id: number;
  name: string;
  description: string | null;
}

// One row from GET /recipes (backend RecipeCard model). Has no `id` — open
// via extract-on-click like SimilarRecipe.
export interface ExploreRecipe {
  title: string;
  source_url: string;
  image_url: string | null;
  prep_time: string | null;
  cook_time: string | null;
  total_time: string | null;
  servings: string | null;
  category: string | null;
}

export interface RecipeListResponse {
  items: ExploreRecipe[];
  next_cursor: string | null;
}

export type ThemeName = "cream" | "dark" | "calico" | "espresso";
