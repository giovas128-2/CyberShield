import type { ReactNode } from "react";
import { Loader2, Inbox, Info } from "lucide-react";
import type { SourceMode } from "../types";
import type { Source } from "../services/management";

export const Loading = ({ text = "Cargando…" }: { text?: string }) => (
  <div className="card mu" style={{ display: "flex", gap: 10, alignItems: "center" }}><Loader2 size={16} className="spin" />{text}</div>
);
export const ErrorState = ({ message, onRetry }: { message: string; onRetry?: () => void }) => (
  <div className="errbox"><b>No se pudo cargar la información</b>{message} {onRetry && <button className="lnk" onClick={onRetry}>Reintentar</button>}</div>
);
export const EmptyState = ({ text }: { text: string }) => <div className="card empty"><Inbox size={40} strokeWidth={1.5} /><div>{text}</div></div>;

// INTEGRADA = flujo real confirmado; SIMULACIÓN CONTROLADA = demo/laboratorio; PENDIENTE = todavía no validado E2E.
export const ModeBadge = ({ mode }: { mode: SourceMode }) => {
  const cfg = mode === "integrated"
    ? { cls: "t-info", text: "INTEGRADA", title: "Integración confirmada con el flujo real disponible." }
    : mode === "pending"
      ? { cls: "t-wn", text: "PENDIENTE", title: "Control preparado, pero todavía no validado de extremo a extremo." }
      : { cls: "t-vio", text: "SIMULACIÓN CONTROLADA", title: "Escenario benigno de laboratorio o datos de demostración." };
  return <span className={`st ${cfg.cls}`} title={cfg.title}>{cfg.text}</span>;
};
export const Pill = ({ tone, children }: { tone: "ok" | "wn" | "er" | "info" | "vio"; children: ReactNode }) => <span className={`st t-${tone}`}>{children}</span>;

export const PageHeader = ({ title, subtitle, children }: { title: string; subtitle?: string; children?: ReactNode }) => (
  <div className="h"><div><h1>{title}</h1>{subtitle && <div className="mu">{subtitle}</div>}</div>{children}</div>
);

/* Estados loading / error / empty / "datos simulados" para cualquier recurso cargado con useResource */
export function ResourceView({ r, empty, children }: {
  r: { loading: boolean; error: string | null; data: unknown[] | null; source: Source | null; reason?: string; reload: () => void }; empty: string; children: ReactNode;
}) {
  if (r.loading && !r.data) return <Loading />;
  if (r.error && !r.data) return <ErrorState message={r.error} onRetry={r.reload} />;
  return (
    <>
      {r.source === "mock" && <div className="demo"><Info size={16} />DATOS SIMULADOS · {r.reason ?? "Datos de demostración."}</div>}
      {r.error && <ErrorState message={r.error} onRetry={r.reload} />}
      {r.data && r.data.length === 0 ? <EmptyState text={empty} /> : children}
    </>
  );
}

export function DataTable<T>({ columns, rows, rowKey }: { columns: { label: string; cell: (r: T) => ReactNode }[]; rows: T[]; rowKey: (r: T) => string }) {
  return (
    <div className="tw"><table>
      <thead><tr>{columns.map((c) => <th key={c.label}>{c.label}</th>)}</tr></thead>
      <tbody>{rows.map((r) => <tr key={rowKey(r)}>{columns.map((c) => <td key={c.label}>{c.cell(r)}</td>)}</tr>)}</tbody>
    </table></div>
  );
}
