import { useState } from "react";
import { UploadCloud, FolderOpen, MessageCircleQuestion, Lock } from "lucide-react";
import ModeBadge from "./components/ModeBadge.jsx";
import UploadScreen from "./components/UploadScreen.jsx";
import DocumentList from "./components/DocumentList.jsx";
import ChatQA from "./components/ChatQA.jsx";

const TABS = [
  { id: "upload", label: "Upload", Icon: UploadCloud },
  { id: "documents", label: "Documents", Icon: FolderOpen },
  { id: "ask", label: "Ask", Icon: MessageCircleQuestion },
];

function Dot() {
  return <span className="h-1 w-1 rounded-full bg-mint" aria-hidden="true" />;
}

export default function App() {
  const [tab, setTab] = useState("upload");

  return (
    <div className="flex min-h-screen">
      <ModeBadge />

      <nav className="sticky top-0 flex h-screen w-60 shrink-0 flex-col border-r border-line/70 px-4 py-7">
        <div className="flex items-center gap-3 px-2">
          <img src="/logo-icon.png" alt="FamilyVault AI" className="h-11 w-11 rounded-xl" />
          <div className="font-display text-lg font-semibold leading-tight tracking-tight">
            FamilyVault <span className="text-gradient">AI</span>
          </div>
        </div>
        <p className="mb-8 mt-3 flex flex-wrap items-center gap-x-1.5 px-2 text-[11px] text-inkFaint">
          Understand <Dot /> Remember <Dot /> Protect
        </p>

        <div className="flex flex-col gap-1">
          {TABS.map(({ id, label, Icon }) => {
            const active = tab === id;
            return (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-left font-medium transition-colors ${
                  active
                    ? "bg-brand/20 text-white ring-1 ring-brand/40"
                    : "text-inkFaint hover:bg-white/5 hover:text-ink"
                }`}
              >
                <Icon size={17} strokeWidth={1.75} className={active ? "text-aqua" : ""} />
                {label}
              </button>
            );
          })}
        </div>

        <div className="mt-auto flex items-start gap-2 rounded-lg border border-line/70 bg-surface/60 p-3 text-xs leading-relaxed text-inkFaint">
          <Lock size={14} className="mt-0.5 shrink-0 text-mint" />
          <span>Documents are processed on this machine unless the badge says Cloud.</span>
        </div>
      </nav>

      <main className="min-w-0 flex-1 px-10 py-10">
        {tab === "upload" && <UploadScreen onViewDocuments={() => setTab("documents")} />}
        {tab === "documents" && <DocumentList />}
        {tab === "ask" && <ChatQA />}
      </main>
    </div>
  );
}
