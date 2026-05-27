export interface Ingredient {
  qty: number;
  unit: string;
  item: string;
}

export interface Recipe {
  id: string;
  title: string;
  source: string;
  color: string;
  timeMin: number;
  servings: number;
  difficulty: string;
  summary: string;
  ingredients: Ingredient[];
  steps: string[];
  timers: Record<number, number>;
}

export type ThemeName = "cream" | "dark" | "calico" | "espresso";
