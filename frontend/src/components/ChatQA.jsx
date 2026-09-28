import { useEffect, useRef, useState } from "react";
import { AlertTriangle, FileText, Send, Sparkles } from "lucide-react";
import { askQuestion } from "../api/client";

const SUGGESTIONS = [
  "When does my insurance expire?",
  "What's my monthly rent?",
  "What documents do I have?",
];

export default function ChatQA() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, asking]);

  async function handleAsk(e) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || asking) return;

    setMessages((prev) => [...prev, { role: "user", text: trimmed }]);
    setQuestion("");
    setAsking(true);

    try {
      const { answer, sources, ollama_mode } = await askQuestion(trimmed);
      setMessages((prev) => [...prev, { role: "assistant", text: answer, sources, mode: ollama_mode }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "assistant", text: err.message, isError: true }]);
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-5rem)] max-w-3xl flex-col">
      <h1 className="mb-6 shrink-0 font-display text-3xl font-semibold tracking-tight">Ask about your documents</h1>

      <div ref={scrollRef} className="mb-5 flex flex-1 flex-col gap-4 overflow-y-auto pr-1">
        {messages.length === 0 && (
          <div className="card flex flex-col items-start gap-4 p-6">
            <span className="flex items-center gap-2 text-sm text-inkFaint">
              <Sparkles size={15} className="text-aqua" />
              Ask anything across all your saved documents. Answers always cite their source.
            </span>
            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => setQuestion(suggestion)}
                  className="rounded-full border border-line bg-raised/60 px-3 py-1.5 text-sm text-ink transition hover:border-aqua/60 hover:text-aqua"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`max-w-[85%] rounded-2xl px-4 py-3 ${
              msg.role === "user"
                ? "self-end rounded-br-md bg-gradient-to-br from-brand to-brand-dark text-white"
                : msg.isError
                  ? "self-start rounded-bl-md border border-danger/40 bg-danger/10"
                  : "card self-start rounded-bl-md"
            }`}
          >
            {msg.isError ? (
              <div className="flex items-start gap-2">
                <AlertTriangle size={16} className="mt-0.5 shrink-0 text-danger" />
                <p className="break-words text-sm">{msg.text}</p>
              </div>
            ) : (
              <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
            )}

            {msg.role === "assistant" && !msg.isError && (
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span
                  className={`rounded-full border px-2 py-0.5 text-xs font-medium ${
                    msg.mode === "cloud"
                      ? "border-cloudflag/40 bg-cloudflag/10 text-cloudflag"
                      : "border-mint/30 bg-mint/10 text-mint"
                  }`}
                >
                  {msg.mode === "cloud" ? "Cloud" : "Local"}
                </span>
                {msg.sources?.map((source) => (
                  <span
                    key={source.document_id}
                    className="inline-flex items-center gap-1 rounded-full border border-line bg-raised/60 px-2 py-0.5 text-xs text-inkFaint"
                  >
                    <FileText size={11} />
                    {source.filename}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}

        {asking && (
          <div className="flex items-center gap-1.5 self-start px-1 text-inkFaint">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-aqua" />
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-aqua [animation-delay:150ms]" />
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-aqua [animation-delay:300ms]" />
            <span className="ml-1 text-sm">Thinking…</span>
          </div>
        )}
      </div>

      <form onSubmit={handleAsk} className="flex shrink-0 gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question…"
          className="input flex-1"
        />
        <button type="submit" disabled={asking || !question.trim()} className="btn-primary">
          <Send size={16} />
          Ask
        </button>
      </form>
    </div>
  );
}
