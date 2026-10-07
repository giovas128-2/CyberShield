import type { Evento } from "../types";

export const SEV: Record<string, string> = {
  BAJA: "Bajo",
  BAJO: "Bajo",
  LOW: "Bajo",
  NORMAL: "Bajo",
  MEDIA: "Medio",
  MEDIO: "Medio",
  MEDIUM: "Medio",
  WARNING: "Medio",
  ALTA: "Alto",
  ALTO: "Alto",
  HIGH: "Alto",
  CRITICA: "Crítico",
  CRITICO: "Crítico",
  CRITICAL: "Crítico",
};

export const sevCls = (s: unknown) => {
  const value = SEV[String(s).toUpperCase()] || String(s);
  return ({ Bajo: "ok", Medio: "wn", Alto: "er", Crítico: "er" } as Record<string, string>)[value] || "ok";
};

export const sevTxt = (s: unknown) => SEV[String(s).toUpperCase()] || String(s);

export const toSeverity = (s: unknown): "BAJA" | "MEDIA" | "ALTA" | "CRITICA" => {
  const v = String(s).toUpperCase();
  if (["CRITICAL", "CRITICA", "CRITICO"].includes(v)) return "CRITICA";
  if (["HIGH", "ALTA", "ALTO"].includes(v)) return "ALTA";
  if (["MEDIUM", "MEDIA", "MEDIO", "WARNING"].includes(v)) return "MEDIA";
  return "BAJA";
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

// Agrupa los created_at reales de /events por minuto. El gráfico conserva el
// estilo original del frontend y deja de usar números aleatorios.
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
