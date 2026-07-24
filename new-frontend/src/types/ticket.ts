export type TicketCategory =
  | "parser"
  | "recipe"
  | "account"
  | "bug"
  | "feature_request"
  | "other";

export type TicketStatus = "open" | "in_progress" | "resolved" | "closed";

export interface TicketDetail {
  id: string;
  category: TicketCategory;
  status: TicketStatus;
  subject: string;
  description: string;
  recipe_url: string | null;
  metadata: Record<string, unknown>;
  submitter_ip_hash: string | null;
  user_agent: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketListResponse {
  items: TicketDetail[];
  total: number;
  limit: number;
  offset: number;
}
