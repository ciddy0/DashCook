import { useCallback, useEffect, useRef, useState } from "react";
import { Icon } from "./Icon";
import {
  ToastContext,
  type ToastContextValue,
  type ToastVariant,
} from "../context/toast-context";

interface ToastState {
  id: number;
  message: string;
  variant: ToastVariant;
}

const DISMISS_MS = 4000;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toast, setToast] = useState<ToastState | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const dismiss = useCallback(() => {
    if (timer.current) clearTimeout(timer.current);
    setToast(null);
  }, []);

  const showToast = useCallback(
    (message: string, variant: ToastVariant = "success") => {
      if (timer.current) clearTimeout(timer.current);
      setToast({ id: Date.now(), message, variant });
      timer.current = setTimeout(() => setToast(null), DISMISS_MS);
    },
    [],
  );

  useEffect(() => {
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);

  const value: ToastContextValue = {
    showToast,
    success: (m) => showToast(m, "success"),
    info: (m) => showToast(m, "info"),
    warning: (m) => showToast(m, "warning"),
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      {toast && (
        <div className="toast-wrap" role="status" aria-live="polite">
          <div className={`banner banner-${toast.variant} toast`} key={toast.id}>
            <div className="toast-msg">{toast.message}</div>
            <button
              className="toast-close"
              onClick={dismiss}
              aria-label="Dismiss notification"
            >
              <Icon name="x" size={16} />
            </button>
          </div>
        </div>
      )}
    </ToastContext.Provider>
  );
}
