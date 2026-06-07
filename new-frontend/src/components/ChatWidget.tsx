import { useState, useRef, useEffect } from "react";
import { searchRecipes } from "../api";
import type { SimilarRecipe } from "../types";

interface Message {
  role: "user" | "bot";
  text?: string;
  recipes?: SimilarRecipe[];
}

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const messagesEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const query = input.trim();
    if (!query || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: query }]);
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

  return (
    <>
      {!open && (
        <button
          className="chat-fab"
          onClick={() => setOpen(true)}
          aria-label="Open chat"
        >
          <img src="/cat.svg" alt="" width={224} height={224} />
        </button>
      )}

      {open && (
        <div className="chat-panel card">
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
            {messages.length === 0 && (
              <div className="chat-empty">
                Search for recipes by describing what you're in the mood for!
              </div>
            )}
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
              placeholder="e.g. summer meals, quick pasta..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              autoFocus
            />
            <button
              className="btn btn-sm chat-send"
              type="submit"
              disabled={!input.trim() || loading}
            >
              Send
            </button>
          </form>
        </div>
      )}
    </>
  );
}
