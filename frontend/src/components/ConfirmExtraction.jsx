import { useMemo, useState } from "react";
import { HelpCircle, Save } from "lucide-react";
import { confirmExtraction } from "../api/client";
import { FIELD_LABELS, docTypeMeta, fieldEntries, isBlank } from "../lib/fields";

export default function ConfirmExtraction({ documentId, explanation, extractedFields, onSaved, onCancel }) {
  const documentType = extractedFields.document_type;
  const meta = docTypeMeta(documentType);
  const [fields, setFields] = useState(extractedFields);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // The fields the model couldn't read -- these are the ones worth the user's attention.
  const missingKeys = useMemo(
    () => new Set(fieldEntries(extractedFields).filter(([, value]) => isBlank(value)).map(([key]) => key)),
    [extractedFields]
  );

  function updateField(key, value) {
    setFields((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      // Blank inputs are saved as null, not empty strings.
      const cleaned = Object.fromEntries(
        Object.entries(fields).map(([key, value]) => [key, value === "" ? null : value])
      );
      await confirmExtraction(documentId, documentType, cleaned);
      onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-3xl">
      <div className="mb-2 flex items-center gap-3">
        <h1 className="font-display text-3xl font-semibold tracking-tight">Review the details</h1>
        <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${meta.chip}`}>{meta.label}</span>
      </div>

      <p className="mb-6 text-inkFaint">
        {missingKeys.size > 0
          ? `We couldn't confidently read ${missingKeys.size} ${
              missingKeys.size === 1 ? "detail" : "details"
            } — highlighted below. Everything else was filled in automatically.`
          : "Review the details below and save any changes."}
      </p>

      {explanation && (
        <div className="card mb-8 p-5">
          <h2 className="section-label mb-2">In plain English</h2>
          <p className="leading-relaxed text-ink/90">{explanation}</p>
        </div>
      )}

      <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {fieldEntries(fields).map(([key, value]) => {
          const needsInput = missingKeys.has(key) && isBlank(value);
          return (
            <label key={key} className="flex flex-col gap-1.5">
              <span className="flex items-center justify-between text-sm font-medium">
                {FIELD_LABELS[key] || key}
                {needsInput && (
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-violet-light">
                    <HelpCircle size={12} />
                    Needs your input
                  </span>
                )}
              </span>
              <input
                type="text"
                value={value ?? ""}
                onChange={(e) => updateField(key, e.target.value)}
                className={`input ${needsInput ? "!border-violet !ring-1 !ring-violet/60" : ""}`}
              />
            </label>
          );
        })}
      </div>

      {missingKeys.size > 0 && (
        <p className="mb-4 text-xs text-inkFaint">
          If a detail genuinely isn't in the document, leave it blank — it will be saved as empty.
        </p>
      )}

      {error && <p className="mb-4 text-sm text-danger">{error}</p>}

      <div className="flex gap-3">
        <button onClick={handleSave} disabled={saving} className="btn-primary">
          <Save size={16} />
          {saving ? "Saving…" : "Confirm and save"}
        </button>
        {onCancel && (
          <button onClick={onCancel} disabled={saving} className="btn-ghost">
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}
