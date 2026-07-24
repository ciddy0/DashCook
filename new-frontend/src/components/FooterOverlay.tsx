import { useEffect } from "react";
import { Icon } from "./Icon";
import { useFocusTrap } from "../hooks/useFocusTrap";

interface FooterOverlayProps {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}

export function FooterOverlay({ title, onClose, children }: FooterOverlayProps) {
  const trapRef = useFocusTrap<HTMLDivElement>();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);

    // Lock background scroll on both html and body
    const prevBody = document.body.style.overflow;
    const prevHtml = document.documentElement.style.overflow;
    document.body.style.overflow = "hidden";
    document.documentElement.style.overflow = "hidden";

    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevBody;
      document.documentElement.style.overflow = prevHtml;
    };
  }, [onClose]);

  return (
    <div
      className="footer-overlay"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      ref={trapRef}
      tabIndex={-1}
    >
      <button className="footer-overlay-close icon-btn" onClick={onClose} aria-label="Close">
        <Icon name="x" size={18} />
      </button>
      <div className="footer-overlay-body">
        <div className="footer-overlay-content">{children}</div>
      </div>
    </div>
  );
}
