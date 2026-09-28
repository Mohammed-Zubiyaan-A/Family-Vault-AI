import { useEffect, useState } from "react";
import { AlertTriangle, Calendar, ChevronDown, ClipboardCheck, Loader2, Trash2 } from "lucide-react";
import { deleteDocument, getDocumentDetail, listDocuments } from "../api/client";
import { FIELD_LABELS, docTypeMeta, fieldEntries } from "../lib/fields";
import ConfirmExtraction from "./ConfirmExtraction.jsx";

// Small badge describing a document's state, when it isn't simply "saved".
function StatusBadge({ doc }) {
  if (doc.status === "error") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-danger/40 bg-danger/10 px-2 py-0.5 text-xs font-medium text-danger">
        <AlertTriangle size={11} /> Failed
      </span>
    );
  }
  if (doc.status === "processing") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-aqua/40 bg-aqua/10 px-2 py-0.5 text-xs font-medium text-aqua">
        <Loader2 size={11} className="animate-spin" /> Processing
      </span>
    );
  }
  if (!doc.confirmed) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-violet/40 bg-violet/15 px-2 py-0.5 text-xs font-medium text-violet-light">
        <ClipboardCheck size={11} /> Needs review
      </span>
    );
  }
  return null;
}

export default function DocumentList() {
  const [documents, setDocuments] = useState(null);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);
  const [details, setDetails] = useState({}); // document_id -> detail response
  const [detailLoading, setDetailLoading] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [reviewingId, setReviewingId] = useState(null);

  function refresh() {
    return listDocuments()
      .then((data) => setDocuments(data.documents))
      .catch((err) => setError(err.message));
  }

  useEffect(() => {
    refresh();
  }, []);

  async function loadDetail(documentId, { force = false } = {}) {
    if (details[documentId] && !force) return details[documentId];
    setDetailLoading(documentId);
    try {
      const detail = await getDocumentDetail(documentId);
      setDetails((prev) => ({ ...prev, [documentId]: detail }));
      return detail;
    } catch (err) {
      const failed = { error: err.message };
      setDetails((prev) => ({ ...prev, [documentId]: failed }));
      return failed;
    } finally {
      setDetailLoading(null);
    }
  }

  async function toggleExpand(documentId) {
    setConfirmDeleteId(null);
    if (expandedId === documentId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(documentId);
    await loadDetail(documentId);
  }

  async function handleDelete(documentId) {
    setDeletingId(documentId);
    setError(null);
    try {
      await deleteDocument(documentId);
      setDocuments((prev) => prev.filter((doc) => doc.document_id !== documentId));
      setDetails((prev) => {
        const next = { ...prev };
        delete next[documentId];
        return next;
      });
      if (expandedId === documentId) setExpandedId(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId(null);
      setConfirmDeleteId(null);
    }
  }

  async function handleReviewSaved() {
    const savedId = reviewingId;
    setReviewingId(null);
    await refresh();
    await loadDetail(savedId, { force: true });
  }

  // Reviewing a document that was saved without confirmation.
  const reviewDetail = reviewingId ? details[reviewingId] : null;
  if (reviewingId && reviewDetail && !reviewDetail.error) {
    return (
      <ConfirmExtraction
        documentId={reviewingId}
        explanation={reviewDetail.explanation}
        extractedFields={{ document_type: reviewDetail.document_type, ...(reviewDetail.fields || {}) }}
        onSaved={handleReviewSaved}
        onCancel={() => setReviewingId(null)}
      />
    );
  }

  return (
    <div className="max-w-3xl">
      <h1 className="mb-6 font-display text-3xl font-semibold tracking-tight">Your documents</h1>

      {error && (
        <p className="mb-4 rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p>
      )}
      {!documents && !error && <p className="text-inkFaint">Loading…</p>}

      {documents && documents.length === 0 && (
        <div className="card flex flex-col items-center gap-3 px-6 py-14 text-center">
          <img src="/logo-icon.png" alt="" className="h-20 w-20 rounded-2xl opacity-90" />
          <p className="font-display text-lg font-medium">Your vault is empty</p>
          <p className="max-w-xs text-sm text-inkFaint">
            Upload a rent agreement, insurance policy or loan document and it will show up here.
          </p>
        </div>
      )}

      <ul className="flex flex-col gap-3">
        {documents?.map((doc) => {
          const meta = docTypeMeta(doc.status === "ready" ? doc.document_type : null);
          const Icon = meta.Icon;
          const isOpen = expandedId === doc.document_id;
          const detail = details[doc.document_id];

          return (
            <li
              key={doc.document_id}
              className={`card overflow-hidden transition-colors ${isOpen ? "border-brand/50" : "hover:border-brand/40"}`}
            >
              <button
                onClick={() => toggleExpand(doc.document_id)}
                className="flex w-full items-center gap-4 p-4 text-left"
              >
                <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${meta.tile}`}>
                  <Icon size={20} strokeWidth={1.75} />
                </span>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <span className="truncate font-display text-lg font-medium">{doc.filename}</span>
                    <StatusBadge doc={doc} />
                  </div>
                  <div className="mt-0.5 flex flex-wrap items-center gap-x-3 text-xs text-inkFaint">
                    {doc.status === "ready" && <span>{meta.label}</span>}
                    {doc.key_dates.length > 0 && (
                      <span className="inline-flex items-center gap-1">
                        <Calendar size={12} /> {doc.key_dates[0]}
                      </span>
                    )}
                  </div>
                  {!isOpen && doc.summary && (
                    <p className="mt-1.5 line-clamp-2 text-sm text-inkFaint">{doc.summary}</p>
                  )}
                </div>

                <ChevronDown
                  size={18}
                  className={`shrink-0 text-inkFaint transition-transform ${isOpen ? "rotate-180" : ""}`}
                />
              </button>

              {isOpen && (
                <div className="border-t border-line/70 bg-night/40 px-5 py-5">
                  {detailLoading === doc.document_id && !detail && (
                    <p className="text-sm text-inkFaint">Loading details…</p>
                  )}
                  {detail?.error && <p className="text-sm text-danger">{detail.error}</p>}

                  {detail && !detail.error && (
                    <>
                      {detail.status === "error" && (
                        <p className="mb-4 rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
                          This document failed to process
                          {detail.error_message ? `: ${detail.error_message}` : "."} You can delete it and try
                          uploading it again.
                        </p>
                      )}

                      {detail.explanation && (
                        <div className="mb-5">
                          <h3 className="section-label mb-2">In plain English</h3>
                          <p className="leading-relaxed text-ink/90">{detail.explanation}</p>
                        </div>
                      )}

                      {detail.fields && (
                        <div className="mb-5">
                          <h3 className="section-label mb-2">Key details</h3>
                          <div className="grid grid-cols-1 gap-x-8 sm:grid-cols-2">
                            {fieldEntries(detail.fields).map(([key, value]) => (
                              <div key={key} className="flex justify-between gap-3 border-b border-line/60 py-2 text-sm">
                                <span className="text-inkFaint">{FIELD_LABELS[key] || key}</span>
                                <span className="text-right font-medium">{value ?? "—"}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {detail.status === "ready" && !detail.confirmed && detail.fields && (
                        <div className="mb-5 flex flex-wrap items-center gap-3 rounded-lg border border-violet/30 bg-violet/10 px-3 py-2.5 text-sm">
                          <span className="flex-1 text-ink/90">
                            Some details couldn't be read with confidence. Review them to finish saving.
                          </span>
                          <button
                            onClick={() => setReviewingId(doc.document_id)}
                            className="btn-primary !px-4 !py-1.5 text-sm"
                          >
                            <ClipboardCheck size={15} />
                            Review &amp; save
                          </button>
                        </div>
                      )}
                    </>
                  )}

                  {/* Delete -- two-step so a stray click can't remove a document */}
                  {confirmDeleteId === doc.document_id ? (
                    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-danger/40 bg-danger/10 px-3 py-2.5 text-sm">
                      <span className="flex-1 text-ink/90">
                        Delete this document and its searchable data? This can't be undone.
                      </span>
                      <button
                        onClick={() => setConfirmDeleteId(null)}
                        disabled={deletingId === doc.document_id}
                        className="btn-ghost !px-4 !py-1.5 text-sm"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleDelete(doc.document_id)}
                        disabled={deletingId === doc.document_id}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-danger px-4 py-1.5 text-sm font-medium text-night transition hover:brightness-110 disabled:opacity-60"
                      >
                        <Trash2 size={14} />
                        {deletingId === doc.document_id ? "Deleting…" : "Yes, delete"}
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setConfirmDeleteId(doc.document_id)}
                      className="inline-flex items-center gap-1.5 text-sm text-danger/90 hover:text-danger hover:underline"
                    >
                      <Trash2 size={15} />
                      Delete document
                    </button>
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
