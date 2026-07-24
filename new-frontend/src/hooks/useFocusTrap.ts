import { useEffect, useRef } from "react";

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * Contains keyboard focus within a dialog for as long as `active` is true, so
 * `aria-modal="true"` actually holds. Attach the returned ref to the dialog
 * container. On activate it moves focus inside (unless focus is already there,
 * e.g. an autofocused field); on deactivate it restores focus to whatever was
 * focused before — pass `restoreFocus: false` for dialogs that unmount by
 * navigating away, where the previous element no longer exists.
 */
export function useFocusTrap<T extends HTMLElement>(
  active = true,
  { restoreFocus = true }: { restoreFocus?: boolean } = {},
) {
  const ref = useRef<T>(null);

  useEffect(() => {
    if (!active) return;
    const container = ref.current;
    if (!container) return;

    const previouslyFocused = document.activeElement as HTMLElement | null;

    const getFocusable = () =>
      Array.from(
        container.querySelectorAll<HTMLElement>(FOCUSABLE),
      ).filter((el) => el.offsetParent !== null);

    // Pull focus into the dialog unless a child already claimed it (autofocus).
    if (!container.contains(document.activeElement)) {
      (getFocusable()[0] ?? container).focus();
    }

    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;
      const focusable = getFocusable();
      if (focusable.length === 0) {
        e.preventDefault();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const activeEl = document.activeElement;
      if (e.shiftKey && (activeEl === first || !container.contains(activeEl))) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && activeEl === last) {
        e.preventDefault();
        first.focus();
      }
    };

    container.addEventListener("keydown", onKey);
    return () => {
      container.removeEventListener("keydown", onKey);
      if (restoreFocus) previouslyFocused?.focus?.();
    };
  }, [active, restoreFocus]);

  return ref;
}
