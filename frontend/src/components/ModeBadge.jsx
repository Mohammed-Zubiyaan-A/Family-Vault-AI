import { useEffect, useState } from "react";
import { Cloud, Cpu } from "lucide-react";
import { getSystemMode } from "../api/client";

export default function ModeBadge() {
  const [mode, setMode] = useState(null);

  useEffect(() => {
    getSystemMode()
      .then(setMode)
      .catch(() => setMode(null));
  }, []);

  if (!mode) return null;

  const isCloud = mode.ollama_mode === "cloud";
  const Icon = isCloud ? Cloud : Cpu;

  return (
    <div
      className={`fixed right-5 top-4 z-50 flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-medium backdrop-blur ${
        isCloud
          ? "border-cloudflag/50 bg-cloudflag/10 text-cloudflag"
          : "border-mint/40 bg-mint/10 text-mint"
      }`}
      title={`Model: ${mode.model}`}
    >
      <Icon size={14} strokeWidth={2} />
      Running: {isCloud ? "Cloud" : "Local"}
    </div>
  );
}
