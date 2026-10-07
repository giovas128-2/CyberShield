import { useEffect } from "react";
import { AlertTriangle, Check, X } from "lucide-react";

export type ToastData = {
  kind: "ok" | "err";
  text: string;
};

export function Toast({
  toast,
  onClose,
}: {
  toast: ToastData | null;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(onClose, 4500);
    return () => window.clearTimeout(timer);
  }, [toast, onClose]);

  if (!toast) return null;

  return (
    <div className={`toast ${toast.kind}`} role="status">
      {toast.kind === "ok" ? <Check size={16} /> : <AlertTriangle size={16} />}
      <span>{toast.text}</span>
      <button onClick={onClose} aria-label="Cerrar aviso">
        <X size={14} />
      </button>
    </div>
  );
}
