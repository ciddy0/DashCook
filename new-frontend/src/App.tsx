import { useState, useEffect, lazy, Suspense } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import { Topbar } from "./components/Topbar";
import { Footer } from "./components/Footer";
import { useClickSound } from "./hooks/useClickSound";
import type { ThemeName } from "./types";

const Home = lazy(() =>
  import("./pages/Home").then((m) => ({ default: m.Home }))
);
const RecipeDetail = lazy(() =>
  import("./pages/RecipeDetail").then((m) => ({ default: m.RecipeDetail }))
);
const CookNow = lazy(() =>
  import("./pages/CookNow").then((m) => ({ default: m.CookNow }))
);
const ChatWidget = lazy(() =>
  import("./components/ChatWidget").then((m) => ({ default: m.ChatWidget }))
);

const THEMES: ThemeName[] = ["cream", "dark", "calico", "espresso"];

function App() {
  useClickSound();
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

      <Suspense fallback={<div className="page" />}>
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
      </Suspense>
      {!isCookMode && (
        <Suspense fallback={null}>
          <ChatWidget />
        </Suspense>
      )}
    </>
  );
}

export default App;
