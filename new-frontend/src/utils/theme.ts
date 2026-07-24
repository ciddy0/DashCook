// Per-shelf swatch color pulled from the theme's category palette, so each shelf
// gets a distinct hue that adapts to the active theme. Assigned by list position
// (not id) so the set stays collision-free; "Other" gets a neutral swatch.
const SHELF_COLORS = [
  "var(--cat-1)",
  "var(--cat-2)",
  "var(--cat-3)",
  "var(--cat-4)",
  "var(--cat-5)",
  "var(--cat-6)",
  "var(--cat-7)",
  "var(--cat-8)",
];

export function shelfColor(index: number, name?: string): string {
  if (name && name.trim().toLowerCase() === "other") return "var(--cat-neutral)";
  return SHELF_COLORS[Math.abs(index) % SHELF_COLORS.length];
}
