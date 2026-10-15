import type { Evento, Severidad } from "../types";

export const SEV: Record<Severidad, string> = {
  NORMAL: "NORMAL",
  WARNING: "WARNING",
  HIGH: "HIGH",
  CRITICAL: "CRITICAL",
};

export const sevCls = (s: unknown) => {
  const value = String(s ?? "NORMAL").toUpperCase();
  return value === "NORMAL" ? "ok" : value === "WARNING" ? "wn" : "er";
};

export const sevTxt = (s: unknown) => toSeverity(s);

export const toSeverity = (s: unknown): Severidad => {
  const v = String(s ?? "").toUpperCase();
  if (["CRITICAL", "CRITICA", "CRITICO"].includes(v)) return "CRITICAL";
  if (["HIGH", "ALTA", "ALTO"].includes(v)) return "HIGH";
  if (["WARNING", "MEDIUM", "MEDIA", "MEDIO"].includes(v)) return "WARNING";
  return "NORMAL";
};

export const emailOk = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
export const hhmm = (d = new Date()) => d.toTimeString().slice(0, 5);

export const stamp = (value?: string | Date) => {
  const date = value ? new Date(value) : new Date();
  return date.toLocaleString("es", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const timeAgo = (value?: string | null) => {
  if (!value) return "Sin actividad";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  const minutes = Math.max(0, Math.floor((Date.now() - date.getTime()) / 60000));
  if (minutes < 1) return "Hace un momento";
  if (minutes < 60) return `Hace ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Hace ${hours} h`;
  return `Hace ${Math.floor(hours / 24)} d`;
};

export function eventsPerMinute(events: Evento[], maxPoints = 15): number[] {
  const counts = new Map<string, number>();
  for (const event of events) {
    if (!event.createdAt) continue;
    const date = new Date(event.createdAt);
    if (Number.isNaN(date.getTime())) continue;
    date.setSeconds(0, 0);
    const key = date.toISOString();
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  const values = [...counts.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([, value]) => value)
    .slice(-maxPoints);
  return values.length ? values : [0];
}
