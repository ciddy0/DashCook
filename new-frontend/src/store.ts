import type { Recipe } from "./types";

const STORAGE_KEY = "souschat.recipes";

function readAll(): Recipe[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function writeAll(recipes: Recipe[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(recipes));
}

export function getRecipes(): Recipe[] {
  return readAll();
}

export function addRecipe(recipe: Recipe): void {
  const recipes = readAll().filter((r) => r.id !== recipe.id);
  recipes.unshift(recipe);
  writeAll(recipes);
}

export function removeRecipe(id: string): void {
  writeAll(readAll().filter((r) => r.id !== id));
}

export function getRecipe(id: string): Recipe | undefined {
  return readAll().find((r) => r.id === id);
}
