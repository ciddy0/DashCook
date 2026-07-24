import type { KeyboardEvent } from "react";

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
