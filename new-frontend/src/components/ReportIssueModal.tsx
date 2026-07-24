import { useEffect, useRef, useState } from "react";
import { FooterOverlay } from "./FooterOverlay";
import { submitTicket } from "../services";
import { useToast } from "../context/toast-context";

const SUBJECT_MAX = 200;
const DESCRIPTION_MAX = 5000;

export function ReportIssueModal({
  recipeUrl,
  onClose,
}: {
  recipeUrl?: string | null;
  onClose: () => void;
}) {
  const toast = useToast();
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const subjectRef = useRef<HTMLInputElement>(null);

  const isValid = subject.trim().length > 0 && description.trim().length > 0;

  // Focus the first field on open. Tab is trapped by the FooterOverlay wrapper.
  useEffect(() => {
    subjectRef.current?.focus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid || submitting) return;

    setSubmitting(true);
    setError("");
    try {
      await submitTicket({
        subject: subject.trim(),
        description: description.trim(),
        recipe_url: recipeUrl,
      });
      setSubject("");
      setDescription("");
      onClose();
      toast.success("Thanks! Your parser issue has been submitted.");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Couldn't submit your report. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <FooterOverlay title="Report an issue" onClose={onClose}>
      <h2>Report an issue</h2>
      <p style={{ color: "var(--text-2)", marginTop: -4, marginBottom: 20 }}>
        Spotted something wrong with this recipe? Let us know and we'll take a
        look.
      </p>

      <form onSubmit={handleSubmit} noValidate>
        <div style={{ marginBottom: 18 }}>
          <label
            htmlFor="report-subject"
            style={{ display: "block", fontWeight: 600, marginBottom: 8 }}
          >
            Subject <span style={{ color: "var(--error)" }} aria-hidden="true">*</span>
          </label>
          <input
            id="report-subject"
            ref={subjectRef}
            className="input"
            value={subject}
            onChange={(e) => {
              setSubject(e.target.value);
              setError("");
            }}
            placeholder="Brief summary of the issue"
            maxLength={SUBJECT_MAX}
            required
            aria-required="true"
            disabled={submitting}
          />
        </div>

        <div style={{ marginBottom: 18 }}>
          <label
            htmlFor="report-description"
            style={{ display: "block", fontWeight: 600, marginBottom: 8 }}
          >
            Description <span style={{ color: "var(--error)" }} aria-hidden="true">*</span>
          </label>
          <textarea
            id="report-description"
            className="input"
            value={description}
            onChange={(e) => {
              setDescription(e.target.value);
              setError("");
            }}
            placeholder="What went wrong? The more detail, the better."
            rows={6}
            maxLength={DESCRIPTION_MAX}
            required
            aria-required="true"
            disabled={submitting}
            style={{ resize: "vertical" }}
          />
        </div>

        {error && (
          <div
            className="banner banner-info"
            role="alert"
            style={{ marginBottom: 18 }}
          >
            <div>{error}</div>
          </div>
        )}

        <div className="row" style={{ gap: 12, justifyContent: "flex-end" }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onClose}
            disabled={submitting}
          >
            Cancel
          </button>
          <button type="submit" className="btn" disabled={!isValid || submitting}>
            {submitting ? "Submitting…" : "Submit report"}
          </button>
        </div>
      </form>
    </FooterOverlay>
  );
}
