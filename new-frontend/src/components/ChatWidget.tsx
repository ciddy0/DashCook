import { useState, useRef, useEffect } from "react";
import { useMatch } from "react-router-dom";
import {
  searchRecipes,
  askRecipeQuestion,
  QA_RATE_LIMITED,
  type QATurn,
} from "../api";
import { getRecipe } from "../store";
import type { SimilarRecipe } from "../types";
import { MochiChatIcon } from "./MochiChatIcon";

interface Message {
  role: "user" | "bot";
  text?: string;
  recipes?: SimilarRecipe[];
}

const EXAMPLE_QUESTIONS = [
  "Can I use oil instead of butter?",
  "Is this freezer-friendly?",
  "How do I know when it's done?",
];

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [rateLimited, setRateLimited] = useState(false);
  const messagesEnd = useRef<HTMLDivElement>(null);

  // Context awareness: on /recipe/:id the widget answers questions about that
  // recipe (Q&A mode); everywhere else it searches for recipes (search mode).
  const match = useMatch("/recipe/:id");
  const recipe = match?.params.id ? getRecipe(match.params.id) : undefined;
  const mode: "qa" | "search" = recipe ? "qa" : "search";
  const recipeId = recipe?.id;

  // A conversation is tied to one context. Reset when the recipe (or mode)
  // changes so Q&A about one recipe never bleeds into another or into search.
  useEffect(() => {
    setMessages([]);
    setRateLimited(false);
    setInput("");
  }, [recipeId]);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open]);

  async function search(query: string) {
    setLoading(true);
    const results = await searchRecipes(query);
    setLoading(false);

    if (results.length > 0) {
      setMessages((prev) => [...prev, { role: "bot", recipes: results }]);
    } else {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "No matching recipes found. Try a different search!" },
      ]);
    }
  }

  async function askAboutRecipe(query: string) {
    if (!recipe) return;
    // History is the prior Q&A already in this conversation.
    const history: QATurn[] = [];
    for (let i = 0; i < messages.length - 1; i++) {
      const m = messages[i];
      const next = messages[i + 1];
      if (m.role === "user" && m.text && next.role === "bot" && next.text) {
        history.push({ question: m.text, answer: next.text });
      }
    }

    setLoading(true);
    try {
      const answer = await askRecipeQuestion(query, recipe, history);
      setMessages((prev) => [...prev, { role: "bot", text: answer }]);
    } catch (err) {
      if (err instanceof Error && err.message === QA_RATE_LIMITED) {
        setRateLimited(true);
        setMessages((prev) => [
          ...prev,
          {
            role: "bot",
            text: "You've used all 5 of today's questions — check back tomorrow!",
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "bot",
            text:
              err instanceof Error
                ? err.message
                : "The assistant is unavailable right now. Please try again later.",
          },
        ]);
      }
    } finally {
      setLoading(false);
    }
  }

  async function send(raw: string) {
    const query = raw.trim();
    if (!query || loading || rateLimited) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: query }]);

    if (mode === "qa") {
      await askAboutRecipe(query);
    } else {
      await search(query);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    send(input);
  }

  return (
    <>
      {!open && (
        <button
          className="chat-fab"
          onClick={() => setOpen(true)}
          aria-label="Open chat"
        >
          <MochiChatIcon className="chat-fab-icon" />
        </button>
      )}

      {open && (
        <div
          className="chat-panel card"
          role="dialog"
          aria-modal="true"
          aria-label="Ask sous chef mochi"
        >
          <div className="chat-header">
            <span className="chat-header-title">Ask sous chef mochi</span>
            <button
              className="chat-header-close"
              onClick={() => setOpen(false)}
              aria-label="Close chat"
            >
              &times;
            </button>
          </div>

          <div className="chat-messages">
            {messages.length === 0 &&
              (mode === "qa" && recipe ? (
                <div className="chat-empty">
                  Ask anything about <b>{recipe.title}</b> — substitutions,
                  timing, doneness, storage. 5 questions a day.
                  <div className="chip-row" style={{ marginTop: "var(--s-4)" }}>
                    {EXAMPLE_QUESTIONS.map((q) => (
                      <button
                        key={q}
                        type="button"
                        className="chip"
                        onClick={() => send(q)}
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="chat-empty">
                  Search for recipes by describing what you're in the mood for!
                </div>
              ))}
            {messages.map((msg, i) =>
              msg.role === "user" ? (
                <div key={i} className="chat-bubble-user">
                  {msg.text}
                </div>
              ) : msg.recipes ? (
                <div key={i} className="chat-bubble-bot">
                  <span className="chat-results-label">
                    Found {msg.recipes.length} recipe{msg.recipes.length !== 1 && "s"}:
                  </span>
                  <ul className="chat-results-list">
                    {msg.recipes.map((r) => (
                      <li key={r.source_url}>
                        <a
                          href={r.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="chat-result-link"
                        >
                          {r.image_url && (
                            <img
                              src={r.image_url}
                              alt=""
                              className="chat-result-thumb"
                            />
                          )}
                          <span>{r.title}</span>
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div key={i} className="chat-bubble-bot">
                  {msg.text}
                </div>
              ),
            )}
            {loading && (
              <div className="chat-bubble-bot chat-typing">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
              </div>
            )}
            <div ref={messagesEnd} />
          </div>

          <form className="chat-input-bar" onSubmit={handleSubmit}>
            <input
              className="input chat-input"
              type="text"
              placeholder={
                mode === "qa"
                  ? rateLimited
                    ? "Daily limit reached"
                    : "Ask about this recipe…"
                  : "e.g. summer meals, quick pasta..."
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading || rateLimited}
              maxLength={mode === "qa" ? 500 : undefined}
              autoFocus
            />
            <button
              className="btn btn-sm chat-send"
              type="submit"
              disabled={!input.trim() || loading || rateLimited}
            >
              {mode === "qa" ? "Ask" : "Send"}
            </button>
          </form>
        </div>
      )}
    </>
  );
}
