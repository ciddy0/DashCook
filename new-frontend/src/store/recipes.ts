import type { Recipe } from "../types";
import { readJson, writeJson } from "../utils/storage";

const STORAGE_KEY = "souschat.recipes";

function readAll(): Recipe[] {
  return readJson<Recipe[]>(localStorage, STORAGE_KEY, []);
}

function writeAll(recipes: Recipe[]): void {
  writeJson(localStorage, STORAGE_KEY, recipes);
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
