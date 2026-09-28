import { useEffect, useRef, useState } from "react";
import { UploadCloud, AlertTriangle, RotateCcw, CheckCircle2, Pencil, Check, Loader2, FolderOpen } from "lucide-react";
import { uploadDocument, getDocumentStatus } from "../api/client";
import { FIELD_LABELS, docTypeMeta, fieldEntries } from "../lib/fields";
import ConfirmExtraction from "./ConfirmExtraction.jsx";

const POLL_INTERVAL_MS = 1500;

// `key` must match the stage strings the backend reports in /status.
const STEPS = [
  { key: "reading document (OCR)", label: "Reading the document", hint: "Extracting the text" },
  { key: "classifying document type", label: "Identifying what it is", hint: "Rent, insurance or loan" },
  { key: "writing plain-English explanation", label: "Writing a plain-English explanation", hint: "The slowest step" },
  { key: "extracting structured fields", label: "Pulling out the key details", hint: "Names, dates and amounts" },
];

function currentStepIndex(stage) {
  const index = STEPS.findIndex((step) => step.key === stage);
  return index === -1 ? 0 : index; // "queued" / unknown -> first step
}

export default function UploadScreen({ onViewDocuments = () => {} }) {
  const [dragOver, setDragOver] = useState(false);
  const [documentId, setDocumentId] = useState(null);
  const [status, setStatus] = useState(null); // null | "processing" | "ready" | "error"
  const [stage, setStage] = useState(null);
  const [elapsedSec, setElapsedSec] = useState(0);
  const [explanation, setExplanation] = useState(null);
  const [extractedFields, setExtractedFields] = useState(null);
  const [confirmed, setConfirmed] = useState(false);
  const [editing, setEditing] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const pollRef = useRef(null);
  const timerRef = useRef(null);

  useEffect(() => {
    return () => {
      clearInterval(pollRef.current);
      clearInterval(timerRef.current);
    };
  }, []);

  function stopTimers() {
    clearInterval(pollRef.current);
    clearInterval(timerRef.current);
  }

  async function handleFile(file) {
    if (!file) return;
    setStatus("processing");
    setStage("queued");
    setElapsedSec(0);
    setExplanation(null);
    setExtractedFields(null);
    setConfirmed(false);
    setEditing(false);
    setErrorMessage(null);

    clearInterval(timerRef.current);
    timerRef.current = setInterval(() => setElapsedSec((s) => s + 1), 1000);

    try {
      const { document_id } = await uploadDocument(file);
      setDocumentId(document_id);
      pollStatus(document_id);
    } catch (err) {
      setStatus("error");
      setErrorMessage(err.message);
      stopTimers();
    }
  }

  function pollStatus(id) {
    clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const data = await getDocumentStatus(id);
        setStage(data.stage);

        if (data.status === "ready" && data.extracted_fields) {
          setStatus("ready");
          setExplanation(data.explanation);
          setExtractedFields(data.extracted_fields);
          setConfirmed(data.confirmed);
          stopTimers();
        } else if (data.status === "error") {
          setStatus("error");
          setErrorMessage(data.error_message);
          stopTimers();
        }
      } catch (err) {
        setStatus("error");
        setErrorMessage(err.message);
        stopTimers();
      }
    }, POLL_INTERVAL_MS);
  }

  function reset() {
    stopTimers();
    setDocumentId(null);
    setStatus(null);
    setStage(null);
    setExplanation(null);
    setExtractedFields(null);
    setConfirmed(false);
    setEditing(false);
    setErrorMessage(null);
  }

  const isDone = status === "ready" && extractedFields && documentId;

  // Every field was extracted with confidence -> already saved, no interruption.
  if (isDone && confirmed && !editing) {
    const meta = docTypeMeta(extractedFields.document_type);
    return (
      <div className="max-w-3xl">
        <div className="mb-2 flex items-center gap-3">
          <CheckCircle2 size={26} className="text-mint" />
          <h1 className="font-display text-3xl font-semibold tracking-tight">Saved automatically</h1>
          <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${meta.chip}`}>{meta.label}</span>
        </div>
        <p className="mb-6 text-inkFaint">
          Every detail was read with confidence, so there was nothing for you to fill in.
        </p>

        {explanation && (
          <div className="card mb-6 p-5">
            <h2 className="section-label mb-2">In plain English</h2>
            <p className="leading-relaxed text-ink/90">{explanation}</p>
          </div>
        )}

        <div className="card mb-6 divide-y divide-line/70 px-4 text-sm">
          {fieldEntries(extractedFields).map(([key, value]) => (
            <div key={key} className="flex justify-between gap-4 py-2.5">
              <span className="text-inkFaint">{FIELD_LABELS[key] || key}</span>
              <span className="text-right font-medium">{value ?? "—"}</span>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap gap-3">
          <button onClick={reset} className="btn-primary">
            <UploadCloud size={16} />
            Upload another
          </button>
          <button onClick={onViewDocuments} className="btn-ghost">
            <FolderOpen size={16} />
            View in Documents
          </button>
          <button onClick={() => setEditing(true)} className="btn-ghost">
            <Pencil size={15} />
            Edit details
          </button>
        </div>
      </div>
    );
  }

  // Something was missing/ambiguous (needs review), or the user chose to edit.
  if (isDone && (!confirmed || editing)) {
    return (
      <ConfirmExtraction
        documentId={documentId}
        explanation={explanation}
        extractedFields={extractedFields}
        onSaved={reset}
        onCancel={editing ? () => setEditing(false) : undefined}
      />
    );
  }

  const activeStep = currentStepIndex(stage);

  return (
    <div className="max-w-3xl">
      <h1 className="mb-2 font-display text-3xl font-semibold tracking-tight">Upload a document</h1>
      <p className="mb-8 text-inkFaint">
        Rent agreements, insurance policies or loan documents. You'll only be asked to review
        something if the details couldn't be read with confidence.
      </p>

      {!status && (
        <label
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            handleFile(e.dataTransfer.files?.[0]);
          }}
          className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed p-16 text-center transition-colors ${
            dragOver ? "border-aqua bg-brand/10" : "border-line hover:border-aqua/60 hover:bg-brand/5"
          }`}
        >
          <span className="flex h-14 w-14 items-center justify-center rounded-full bg-raised text-aqua">
            <UploadCloud size={28} strokeWidth={1.5} />
          </span>
          <span className="font-display text-lg font-medium">Drop a file here, or click to choose</span>
          <span className="text-sm text-inkFaint">PDF, JPG or PNG</span>
          <input
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
        </label>
      )}

      {status === "processing" && (
        <div className="card p-6">
          <ol className="flex flex-col gap-4">
            {STEPS.map((step, index) => {
              const done = index < activeStep;
              const active = index === activeStep;
              return (
                <li key={step.key} className="flex items-center gap-3">
                  <span
                    className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                      done
                        ? "bg-mint/15 text-mint"
                        : active
                          ? "bg-brand/20 text-aqua"
                          : "bg-raised text-inkFaint/60"
                    }`}
                  >
                    {done ? (
                      <Check size={15} strokeWidth={2.5} />
                    ) : active ? (
                      <Loader2 size={15} className="animate-spin" />
                    ) : (
                      <span className="h-1.5 w-1.5 rounded-full bg-current" />
                    )}
                  </span>
                  <div className={active || done ? "" : "opacity-50"}>
                    <div className="font-medium">{step.label}</div>
                    {active && <div className="text-xs text-inkFaint">{step.hint}</div>}
                  </div>
                </li>
              );
            })}
          </ol>
          <p className="mt-6 border-t border-line/70 pt-4 text-xs text-inkFaint">
            {elapsedSec}s elapsed
            {elapsedSec > 45 ? " — larger cloud models can take a while, hang tight." : ""}
          </p>
        </div>
      )}

      {status === "error" && (
        <div className="rounded-xl border border-danger/40 bg-danger/10 p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle size={20} className="mt-0.5 shrink-0 text-danger" />
            <div>
              <p className="font-medium text-danger">Something went wrong processing this document.</p>
              {errorMessage && <p className="mt-1 break-words text-sm text-ink/80">{errorMessage}</p>}
            </div>
          </div>
          <button onClick={reset} className="btn-ghost mt-4 !px-4 !py-2 text-sm">
            <RotateCcw size={14} />
            Try another file
          </button>
        </div>
      )}
    </div>
  );
}
