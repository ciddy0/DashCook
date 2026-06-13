import { useState } from "react";
import {
  TermsPage,
  PrivacyPage,
  SecurityPage,
  PatchNotesPage,
  CreditsPage,
  AboutPage,
} from "../pages/FooterPages";

type OverlayId = "terms" | "privacy" | "security" | "patch-notes" | "credits" | "about";

const FOOTER_LINKS: { label: string; id: OverlayId }[] = [
  { label: "Terms", id: "terms" },
  { label: "Privacy", id: "privacy" },
  { label: "Security", id: "security" },
  { label: "Patch Notes", id: "patch-notes" },
  { label: "Credits", id: "credits" },
  { label: "About", id: "about" },
];

const OVERLAY_COMPONENTS: Record<OverlayId, React.FC<{ onClose: () => void }>> = {
  terms: TermsPage,
  privacy: PrivacyPage,
  security: SecurityPage,
  "patch-notes": PatchNotesPage,
  credits: CreditsPage,
  about: AboutPage,
};

export function Footer() {
  const [active, setActive] = useState<OverlayId | null>(null);
  const ActiveOverlay = active ? OVERLAY_COMPONENTS[active] : null;

  return (
    <>
      <footer className="site-footer" role="contentinfo">
        <nav className="footer-links">
          {FOOTER_LINKS.map(({ label, id }, i) => (
            <span key={id}>
              {i > 0 && <span className="footer-dot" aria-hidden="true">&middot;</span>}
              <button className="footer-link" onClick={() => setActive(id)}>
                {label}
              </button>
            </span>
          ))}
        </nav>
      </footer>
      {ActiveOverlay && <ActiveOverlay onClose={() => setActive(null)} />}
    </>
  );
}
