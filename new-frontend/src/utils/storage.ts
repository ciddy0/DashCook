// Safe JSON read/write over a Web Storage area. Any error (private mode, quota,
// disabled storage, malformed JSON) is swallowed so callers fall back gracefully.
export function readJson<T>(storage: Storage, key: string, fallback: T): T {
  try {
    const raw = storage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

export function writeJson<T>(storage: Storage, key: string, value: T): void {
  try {
    storage.setItem(key, JSON.stringify(value));
  } catch {
    // storage unavailable or full — skip persisting, caller still works
  }
}

// Session-scoped JSON cache. Lives until the tab is closed; any storage error
// is swallowed so callers fall back to network.
export function readSessionCache<T>(key: string): T | null {
  return readJson<T | null>(sessionStorage, key, null);
}

export function writeSessionCache<T>(key: string, value: T): void {
  writeJson(sessionStorage, key, value);
}
