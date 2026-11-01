import { useEffect, useRef, useState, type ButtonHTMLAttributes, type ReactNode } from "react";
import { AlertTriangle, CheckCircle2, Info, Lock, ScanLine, X, type LucideIcon } from "lucide-react";
import { useLocation } from "react-router-dom";
import { useIncident } from "./IncidentContext";
import {
  ACTION_LABEL, GLOBAL_BLOCKED, PHASE_LABEL, SCENARIOS, type ActionId, type ModuleId, type Phase,
} from "./incident";
import { employeeMessage, summaryMessage } from "./employeeMessaging";
import "./incident.css";

type Active = Exclude<Phase, "NORMAL">;
const ICON: Record<Active, LucideIcon> = {
  DETECTED: Info,
  LOCKDOWN: AlertTriangle,
  RESPONDING: ScanLine,
  CONTAINED: CheckCircle2,
  FAILED: AlertTriangle,
};

interface LockableProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  action: ActionId;
  module: ModuleId;
  children: ReactNode;
}

/** Botón de negocio: mantiene la acción bloqueada, pero no revela la causa técnica al empleado. */
export function LockableButton({ action, module, className = "ed-btn", children, ...rest }: LockableProps) {
  const { locked } = useIncident();
  const off = locked(action, module);
  return (
    <button
      {...rest}
      className={`${className} ${off ? "is-locked" : ""}`}
      disabled={off || rest.disabled}
      aria-disabled={off || rest.disabled}
      title={off ? "Función temporalmente restringida" : rest.title}
    >
      {off && <Lock size={14} aria-hidden="true" />}
      {children}
      {off && <span className="sr-only"> (función temporalmente restringida)</span>}
    </button>
  );
}

/** Aviso contextual para el empleado. Nunca muestra ataque, MITRE, severidad, IP, comando ni acción defensiva. */
export function IncidentBanner({ module }: { module: ModuleId }) {
  const { state, scenario } = useIncident();
  if (!scenario || state.phase === "NORMAL") return null;
  const phase = state.phase as Active;
  const msg = employeeMessage(scenario, phase, module, state.global);
  const Icon = ICON[phase];
  return (
    <div className={`inc-banner ${msg.tone}`} role="status" aria-live="polite">
      <Icon size={18} aria-hidden="true" />
      <div>
        <div className="inc-head"><b>{msg.title}</b><span className="inc-tag">{msg.label}</span></div>
        <div>{msg.body}</div>
        {msg.support && <small>Soporte interno puede ayudarle si necesita continuar con una función restringida.</small>}
      </div>
    </div>
  );
}

/** Aviso transversal del resumen: informa disponibilidad sin revelar el incidente. */
export function EmployeeSummaryBanner() {
  const { state, scenario } = useIncident();
  if (!scenario || state.phase === "NORMAL") return null;
  const phase = state.phase as Active;
  const msg = summaryMessage(phase);
  const Icon = ICON[phase];
  return (
    <div className={`inc-banner ${msg.tone}`} role="status" aria-live="polite">
      <Icon size={18} aria-hidden="true" />
      <div>
        <div className="inc-head"><b>{msg.title}</b><span className="inc-tag">{msg.label}</span></div>
        <div>{msg.body}</div>
      </div>
    </div>
  );
}

/**
 * Aviso de restricción amplia. Las restricciones siguen vivas en la lógica,
 * pero el empleado puede cerrar el aviso y continuar con las funciones permitidas.
 */
export function LockdownOverlay() {
  const { state } = useIncident();
  const [closed, setClosed] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const visible = state.global && state.phase !== "NORMAL" && !closed;
  useEffect(() => setClosed(false), [state.phase, state.global]);
  useEffect(() => { if (visible) box.current?.focus(); }, [visible]);
  if (!visible) return null;
  const phase = state.phase as Active;
  const msg = summaryMessage(phase);
  const Icon = ICON[phase];
  return (
    <div className="inc-scrim" role="dialog" aria-modal="true" aria-labelledby="inc-title">
      <div className="inc-modal" ref={box} tabIndex={-1}>
        <div className={`inc-banner ${msg.tone}`}>
          <Icon size={18} aria-hidden="true" />
          <div>
            <div className="inc-head"><b id="inc-title">{msg.title}</b><span className="inc-tag">{msg.label}</span></div>
            <div>{msg.body}</div>
          </div>
        </div>
        <div>
          <b>Acciones que pueden aparecer temporalmente no disponibles</b>
          <div className="inc-locks" style={{ marginTop: 8 }}>
            {GLOBAL_BLOCKED.map((a) => <span key={a} className="ed-btn is-locked"><Lock size={14} aria-hidden="true" />{ACTION_LABEL[a]}</span>)}
          </div>
        </div>
        <small>Las funciones no afectadas permanecen disponibles según los permisos de su cuenta.</small>
        <div className="inc-actions">
          <button className="ed-btn pri" onClick={() => setClosed(true)}>Entendido</button>
        </div>
      </div>
    </div>
  );
}

/**
 * Herramienta exclusiva para exposición/laboratorio.
 * NO se muestra en la interfaz normal del empleado.
 * Para habilitarla una vez: #/empresa-demo/inicio?presenter=1
 */
export function SimPanel() {
  const { state, scenario, send } = useIncident();
  const loc = useLocation();
  const [presenter, setPresenter] = useState(() => {
    const q = new URLSearchParams(loc.search).get("presenter") === "1";
    return q || sessionStorage.getItem("ed-presenter") === "1";
  });
  const [pick, setPick] = useState(SCENARIOS[0].id);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (new URLSearchParams(loc.search).get("presenter") === "1") {
      sessionStorage.setItem("ed-presenter", "1");
      setPresenter(true);
    }
  }, [loc.search]);

  if (!presenter) return null;
  const p = state.phase;
  if (!open) return <button className="ed-btn inc-fab" onClick={() => setOpen(true)}>Panel del expositor</button>;

  return (
    <aside className="inc-sim" aria-label="Panel del expositor">
      <div className="inc-head"><b>PANEL DEL EXPOSITOR · SOLO DEMO</b><button className="ed-menu-x" aria-label="Minimizar panel" onClick={() => setOpen(false)}><X size={16} /></button></div>
      <span className="inc-tag" style={{ justifySelf: "start" }}>FUERA DE LA VISTA DEL EMPLEADO</span>
      <small>Este panel conserva el estado técnico solo para demostrar el laboratorio. No forma parte de la experiencia del usuario final.</small>
      <label htmlFor="inc-sc">Escenario de laboratorio</label>
      <select id="inc-sc" className="ed-in" value={pick} onChange={(e) => setPick(e.target.value)} disabled={p !== "NORMAL"}>
        {SCENARIOS.map((s) => <option key={s.id} value={s.id}>{String(s.num).padStart(2, "0")} · {s.title}</option>)}
      </select>
      <div className="inc-state">Estado técnico: <b>{PHASE_LABEL[p]}</b>{scenario && <> · {scenario.script}</>}{state.global && " · GLOBAL"}</div>
      <div className="inc-btns">
        <button className="ed-btn pri" disabled={p !== "NORMAL"} onClick={() => send({ type: "start", id: pick })}>1 · Iniciar escenario</button>
        <button className="ed-btn" disabled={p !== "DETECTED" && p !== "LOCKDOWN"} onClick={() => send({ type: "advance" })}>{p === "DETECTED" ? "2 · Aplicar restricción" : "3 · Verificar respuesta"}</button>
        <button className="ed-btn" disabled={p !== "RESPONDING"} onClick={() => send({ type: "resolve", branch: "A" })}>Rama A · Confirmación recibida</button>
        <button className="ed-btn" disabled={p !== "RESPONDING"} onClick={() => send({ type: "resolve", branch: "B" })}>Rama B · Verificación fallida</button>
        {scenario?.canEscalate && <button className="ed-btn" disabled={state.global || p === "NORMAL" || p === "CONTAINED"} onClick={() => send({ type: "escalate" })}>Escalar restricción global</button>}
        <button className="ed-btn" disabled={p === "NORMAL"} onClick={() => send({ type: "reset" })}>Reiniciar escenario</button>
        <button className="ed-btn" onClick={() => { sessionStorage.removeItem("ed-presenter"); setPresenter(false); }}>Salir del modo expositor</button>
      </div>
    </aside>
  );
}
