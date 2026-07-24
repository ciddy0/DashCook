import type { TicketListResponse } from "../types";
import { apiUrl, postJson } from "./client";

export const UNAUTHORIZED = "UNAUTHORIZED";

export interface TicketInput {
  subject: string;
  description: string;
  recipe_url?: string | null;
}

export async function submitTicket(input: TicketInput): Promise<void> {
  const res = await postJson("/tickets", {
    category: "parser",
    subject: input.subject,
    description: input.description,
    ...(input.recipe_url ? { recipe_url: input.recipe_url } : {}),
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

export async function listTickets(opts: {
  token: string;
  limit?: number;
  offset?: number;
  category?: string;
  status?: string;
  search?: string;
}): Promise<TicketListResponse> {
  const res = await fetch(
    apiUrl("/tickets", {
      limit: opts.limit,
      offset: opts.offset,
      category: opts.category,
      status: opts.status,
      search: opts.search,
    }),
    { headers: { "X-Admin-Token": opts.token } },
  );

  if (res.status === 401) throw new Error(UNAUTHORIZED);
  if (res.status === 503) {
    throw new Error("The tickets endpoint is not enabled on the server.");
  }
  if (!res.ok) throw new Error("Couldn't load tickets. Please try again.");
  return res.json();
}
