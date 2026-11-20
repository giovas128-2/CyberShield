import { useMemo } from "react";
import type { Severidad } from "../types";
import { usePreferences } from "../preferences/cybershieldPreferences";

/** Un único origen para TODOS los filtros; incluye migración MEDIUM/LOW. */
export function useVisibleSeverities(): ReadonlySet<Severidad> {
  const prefs = usePreferences();
  return useMemo(() => new Set(prefs.severities), [prefs.severities]);
}
