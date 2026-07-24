import type { Recipe } from "../types";
import { postJson } from "./client";

export const QA_RATE_LIMITED = "QA_RATE_LIMITED";

export interface QATurn {
  question: string;
  answer: string;
}

export async function askRecipeQuestion(
  question: string,
  recipe: Recipe,
  history: QATurn[] = [],
): Promise<string> {
  const res = await postJson("/ask", {
    question,
    title: recipe.title,
    servings: recipe.servings,
    total_time: recipe.total_time,
    ingredients: recipe.ingredients.map((ing) => ing.raw || ing.name),
    instructions: recipe.instructions,
    history: history.slice(-8),
  });

  if (!res.ok) {
    if (res.status === 429) throw new Error(QA_RATE_LIMITED);
    if (res.status === 422) {
      throw new Error("That question was a bit too long. Try a shorter one.");
    }
    throw new Error("The assistant is unavailable right now. Please try again later.");
  }

  const data = await res.json();
  return (data.answer ?? "").trim();
}
