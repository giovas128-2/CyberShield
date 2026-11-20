/** CyberShield: preferencias PERSONALES de interfaz; nunca cambian controles del backend. */
import { useEffect, useState } from "react";
import type { Severidad } from "../types";

export const SEVERITIES: Severidad[] = ["CRITICAL", "HIGH", "WARNING", "NORMAL"];
export type Theme = "dark" | "light";
export type Density = "comfortable" | "compact";
export type TimeZoneChoice = "browser" | "America/Mexico_City" | "America/Monterrey" | "America/Tijuana" | "UTC";
export interface Preferences {
  newEvents: boolean;
  incidentChanges: boolean;
  saveConfirmation: boolean;
  severities: Severidad[];
  consoleNotices: boolean;
  browserNotices: boolean;
  density: Density;
  theme: Theme;
  timeZone: TimeZoneChoice;
}

export const DEFAULT_PREFERENCES: Preferences = {
  newEvents: true,
  incidentChanges: true,
  saveConfirmation: true,
  severities: ["CRITICAL", "HIGH", "WARNING"],
  consoleNotices: true,
  browserNotices: false,
  density: "comfortable",
  theme: "dark",
  timeZone: "browser",
};

const CHANGE_EVENT = "cybershield:preferences-updated";
const ALLOWED_ZONES: TimeZoneChoice[] = ["browser", "America/Mexico_City", "America/Monterrey", "America/Tijuana", "UTC"];

export function preferenceKey(): string {
  try {
    const user = JSON.parse(localStorage.getItem("cs_user") || "null");
    const name = typeof user?.name === "string" ? user.name : "Usuario de CyberShield";
    return `cs_preferences_${String(user?.id ?? user?.email ?? name)}`;
  } catch {
    return "cs_preferences_user";
  }
}

function normalize(raw: unknown): Preferences {
  const v = raw && typeof raw === "object" ? (raw as Record<string, unknown>) : {};
  const selected = Array.isArray(v.severities) ? v.severities : DEFAULT_PREFERENCES.severities;
  const normalized = selected.map((x) => {
    const s = String(x).toUpperCase();
    return s === "MEDIUM" ? "WARNING" : s === "LOW" ? "NORMAL" : s;
  });
  return {
    newEvents: typeof v.newEvents === "boolean" ? v.newEvents : true,
    incidentChanges: typeof v.incidentChanges === "boolean" ? v.incidentChanges : true,
    saveConfirmation: typeof v.saveConfirmation === "boolean" ? v.saveConfirmation : true,
    severities: SEVERITIES.filter((s) => normalized.includes(s)),
    consoleNotices: typeof v.consoleNotices === "boolean" ? v.consoleNotices : true,
    browserNotices: v.browserNotices === true,
    density: v.density === "compact" ? "compact" : "comfortable",
    theme: v.theme === "light" ? "light" : "dark",
    timeZone: ALLOWED_ZONES.includes(v.timeZone as TimeZoneChoice) ? v.timeZone as TimeZoneChoice : "browser",
  };
}

export function getPreferences(): Preferences {
  try {
    return normalize(JSON.parse(localStorage.getItem(preferenceKey()) || "null"));
  } catch {
    return normalize(null);
  }
}

export function savePreferences(prefs: Preferences): void {
  // Se valida antes de persistir; nunca guarda contraseñas, tokens ni claves de servicio.
  localStorage.setItem(preferenceKey(), JSON.stringify(normalize(prefs)));
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

export function usePreferences(): Preferences {
  const [preferences, setPreferences] = useState(getPreferences);
  useEffect(() => {
    const refresh = () => setPreferences(getPreferences());
    window.addEventListener(CHANGE_EVENT, refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener(CHANGE_EVENT, refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);
  return preferences;
}

export function resolvedTimeZone(): string {
  const selection = getPreferences().timeZone;
  if (selection !== "browser") return selection;
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
}

export function formatClock(value: string | number | Date, withSeconds = false): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("es-MX", {
    timeZone: resolvedTimeZone(), hour: "2-digit", minute: "2-digit",
    second: withSeconds ? "2-digit" : undefined,
    hour12: false,
  }).format(date);
}

export function formatDateTime(value: string | number | Date): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("es-MX", {
    timeZone: resolvedTimeZone(), day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", hour12: false,
  }).format(date);
}

export function currentUserDisplay(): {name: string; role: string} {
  try {
    const u = JSON.parse(localStorage.getItem("cs_user") || "null");
    return {
      name: typeof u?.name === "string" ? u.name : "Usuario de CyberShield",
      role: typeof u?.role === "string" ? u.role : "Usuario autenticado",
    };
  } catch {
    return { name: "Usuario de CyberShield", role: "Usuario autenticado" };
  }
}
