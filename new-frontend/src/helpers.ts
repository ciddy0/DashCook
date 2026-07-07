import type { KeyboardEvent } from "react";
import type { Ingredient } from "./types";

/**
 * Returns an onKeyDown handler that activates `fn` on Enter or Space,
 * for making non-<button> elements (with role="button") keyboard-operable.
 */
export function onActivateKey(fn: () => void) {
  return (e: KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fn();
    }
  };
}

// Stable per-category color pulled from the theme palette, so each shelf keeps
// the same swatch across renders and adapts to the active theme.
const SHELF_COLORS = [
  "var(--primary)",
  "var(--accent)",
  "var(--success)",
  "var(--warning)",
  "var(--error)",
  "var(--info)",
];

export function shelfColor(categoryId: number): string {
  return SHELF_COLORS[Math.abs(categoryId) % SHELF_COLORS.length];
}

// Session-scoped JSON cache. Lives until the tab is closed; any storage error
// (private mode, quota, disabled) is swallowed so callers fall back to network.
export function readSessionCache<T>(key: string): T | null {
  try {
    const raw = sessionStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

export function writeSessionCache<T>(key: string, value: T): void {
  try {
    sessionStorage.setItem(key, JSON.stringify(value));
  } catch {
    // storage unavailable or full — skip caching, network still works
  }
}

const fractions: Record<string, string> = {
  "0.125": "\u215B",
  "0.25": "\u00BC",
  "0.333": "\u2153",
  "0.375": "\u215C",
  "0.5": "\u00BD",
  "0.625": "\u215D",
  "0.667": "\u2154",
  "0.75": "\u00BE",
  "0.875": "\u215E",
};

export function fmtQty(qty: number, unit?: string): string {
  if (!qty && qty !== 0) return "";
  const whole = Math.floor(qty);
  const frac = qty - whole;
  let nearest: string | null = null;
  let dist = 1;
  for (const k of Object.keys(fractions)) {
    const v = parseFloat(k);
    if (Math.abs(v - frac) < dist) {
      dist = Math.abs(v - frac);
      nearest = k;
    }
  }
  let str: string;
  if (frac < 0.04) str = `${whole}`;
  else if (dist < 0.04 && nearest)
    str = whole > 0 ? `${whole}${fractions[nearest]}` : fractions[nearest];
  else str = (Math.round(qty * 100) / 100).toString();
  return unit ? `${str} ${unit}` : str;
}

export function fmtTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

export function ingredientLine(
  ing: Ingredient,
  scale: number
): { qty: string; item: string } {
  const q = ing.quantity ? ing.quantity * scale : 0;
  const qtyStr = q ? fmtQty(q, ing.unit ?? undefined) : "";
  return { qty: qtyStr, item: ing.name };
}
