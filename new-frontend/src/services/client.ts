const API_BASE =
  "https://dashcook-api.happygrass-bd874e33.westus3.azurecontainerapps.io";

export { API_BASE };

/** Build a full endpoint URL, optionally with query params. */
export function apiUrl(
  path: string,
  params?: Record<string, string | number | null | undefined>,
): string {
  const url = `${API_BASE}${path}`;
  if (!params) return url;

  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value != null && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `${url}?${query}` : url;
}

/** POST a JSON body to an endpoint. */
export function postJson(path: string, body: unknown): Promise<Response> {
  return fetch(apiUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
