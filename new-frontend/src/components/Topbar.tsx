import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Logo } from "./Logo";
import { Icon } from "./Icon";
import kofi from "../assets/kofi.png";
import type { ThemeName } from "../types";

const THEME_OPTIONS: { name: ThemeName; label: string; swatch: string }[] = [
  { name: "cream", label: "Cream", swatch: "#8B5E3C" },
  { name: "dark", label: "Dark", swatch: "#C39267" },
  { name: "calico", label: "Calico", swatch: "#C96B5C" },
  { name: "espresso", label: "Espresso", swatch: "#6E4B3A" },
];

interface TopbarProps {
  theme: ThemeName;
  onSetTheme: (t: ThemeName) => void;
}

export function Topbar({ theme, onSetTheme }: TopbarProps) {
  const navigate = useNavigate();
  const goHome = () => navigate("/");

  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("click", handleClick, true);
    return () => document.removeEventListener("click", handleClick, true);
  }, [open]);

  return (
    <header className="topbar">
      <div className="topbar-inner">
        <Logo onClick={goHome} />
        <div className="spacer" />

        <div className="theme-dropdown" ref={dropdownRef}>
          <button
            className="icon-btn"
            onClick={() => setOpen((v) => !v)}
            title={`Theme: ${theme}`}
            aria-expanded={open}
          >
            <Icon name="palette" size={20} />
          </button>
          {open && (
            <div className="theme-dropdown-menu">
              {THEME_OPTIONS.map((t) => (
                <button
                  key={t.name}
                  className={`theme-option${t.name === theme ? " is-active" : ""}`}
                  onClick={() => {
                    onSetTheme(t.name);
                    setOpen(false);
                  }}
                >
                  <span
                    className="theme-swatch"
                    style={{ background: t.swatch }}
                  />
                  {t.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <a
          className="icon-btn"
          href="https://ko-fi.com/yourhandle"
          target="_blank"
          rel="noopener noreferrer"
        >
          <img src={kofi} alt="Ko-fi" width={24} height={24} />
        </a>
        <button className="btn btn-secondary btn-sm" onClick={goHome}>
          Home
        </button>
      </div>
    </header>
  );
}
