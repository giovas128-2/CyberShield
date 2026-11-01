import { createContext, useContext, useMemo, useReducer, type ReactNode } from "react";
import {
  INITIAL_INCIDENT, findScenario, incidentReducer, isLocked,
  type ActionId, type IncidentEvent, type IncidentState, type ModuleId, type Scenario,
} from "./incident";

interface IncidentCtx {
  state: IncidentState;
  scenario: Scenario | null;
  send: (e: IncidentEvent) => void;
  locked: (action: ActionId, module: ModuleId) => boolean;
}

const Ctx = createContext<IncidentCtx | null>(null);

/* Se monta dentro de EmpresaDemoLayout para que el estado sobreviva al navegar entre módulos.
   Vive solo en memoria: al recargar la página vuelve a NORMAL. */
export function IncidentProvider({ children }: { children: ReactNode }) {
  const [state, send] = useReducer(incidentReducer, INITIAL_INCIDENT);
  const value = useMemo<IncidentCtx>(() => ({
    state, send,
    scenario: findScenario(state.scenarioId),
    locked: (action, module) => isLocked(state, action, module),
  }), [state]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useIncident(): IncidentCtx {
  const c = useContext(Ctx);
  if (!c) throw new Error("useIncident debe usarse dentro de <IncidentProvider>");
  return c;
}
