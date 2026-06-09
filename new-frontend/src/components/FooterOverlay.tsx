import { useEffect } from "react";
import { Icon } from "./Icon";

interface FooterOverlayProps {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}

export function FooterOverlay({ title, onClose, children }: FooterOverlayProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);

    // Lock background scroll
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [onClose]);

  return (
    <div className="footer-overlay" role="dialog" aria-modal="true" aria-label={title}>
      <button className="footer-overlay-close icon-btn" onClick={onClose} aria-label="Close">
        <Icon name="x" size={18} />
      </button>
      <div className="footer-overlay-body">
        <div className="footer-overlay-content">{children}</div>
      </div>
    </div>
  );
}
