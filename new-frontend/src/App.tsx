import { useState, useEffect } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import { Topbar } from "./components/Topbar";
import { Footer } from "./components/Footer";
import { Home } from "./pages/Home";
import { RecipeDetail } from "./pages/RecipeDetail";
import { CookNow } from "./pages/CookNow";
import type { ThemeName } from "./types";

const THEMES: ThemeName[] = ["cream", "dark", "calico", "espresso"];

function App() {
  const location = useLocation();
  const isCookMode = location.pathname.startsWith("/cook/");

  const [theme, setTheme] = useState<ThemeName>(() => {
    const stored = localStorage.getItem("souschat.theme");
    return THEMES.includes(stored as ThemeName) ? (stored as ThemeName) : "cream";
  });

  useEffect(() => {
    localStorage.setItem("souschat.theme", theme);
    for (const t of THEMES) {
      document.body.classList.remove(`theme-${t}`);
    }
    if (theme !== "cream") {
      document.body.classList.add(`theme-${theme}`);
    }
  }, [theme]);

  const [saved, setSaved] = useState<Record<string, boolean>>(() => {
    try {
      return JSON.parse(localStorage.getItem("souschat.saved") || "{}");
    } catch {
      return {};
    }
  });

  // seed defaults for demo
  useEffect(() => {
    if (Object.keys(saved).length === 0) {
      setSaved({ "olive-oil-cake": true, "miso-soup": true });
    }
  }, []);

  // persist
  useEffect(() => {
    try {
      localStorage.setItem("souschat.saved", JSON.stringify(saved));
    } catch {

    }
  }, [saved]);

  const toggleSave = (id: string) =>
    setSaved((s) => ({ ...s, [id]: !s[id] }));

  return (
    <>
      {!isCookMode && (
        <Topbar theme={theme} onSetTheme={setTheme} />
      )}

      <Routes>
        <Route
          path="/"
          element={<Home saved={saved} onToggleSave={toggleSave} />}
        />
        <Route
          path="/recipe/:id"
          element={
            <RecipeDetail saved={saved} onToggleSave={toggleSave} />
          }
        />
        <Route path="/cook/:id" element={<CookNow />} />
      </Routes>

      {!isCookMode && <Footer />}
    </>
  );
}

export default App;
