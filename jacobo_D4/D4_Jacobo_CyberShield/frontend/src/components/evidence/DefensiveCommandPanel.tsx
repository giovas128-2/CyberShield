import { AlertTriangle, Cpu, Database, Flame, Info, Lock, Activity, ShieldCheck, Terminal, TerminalSquare } from "lucide-react";
import type { IncidentEvidence } from "../../types/evidence";
import { actionLabel, eventLabel, hms, isAtRisk, levelClass, statusVisual } from "./evidenceUtils";

const TOOL_ICON = [Activity, Flame, ShieldCheck, Database, Cpu];

/* Pantalla 2 · Comando defensivo del incidente ACTUAL. Solo se renderiza lo que trae `ev.response`
   (command_display / terminal_lines / action_type); el frontend no contiene comandos de ningún ataque. */
export function DefensiveCommandPanel({ ev }: { ev: IncidentEvidence }) {
  const r = ev.response;
  const sv = statusVisual(ev.status); // texto/tono/ícono del estado: STATUS_VISUAL (evidenceUtils.ts)
  const state = { t: sv.responseLabel, c: sv.tone };
  const lines = r.terminal_lines;
  const atRisk = isAtRisk(ev); // D3: en FAILED/ESCALATED la pantalla muestra "Comando intentado" + error sanitizado
  const preview = r.command_preview ?? r.command_display; // BACKEND_GISS: command_preview <- backend.response_action.command_preview
  return (
    <section className="card ev-pane" aria-labelledby="ev-p2">
      <div className="ev-head">
        <span className="ev-ico"><TerminalSquare size={22} /></span>
        <div><h2 id="ev-p2">Pantalla 2 · Comando defensivo asociado al incidente</h2><small className="mu">CyberShield muestra únicamente el comando de respuesta vinculado al ataque detectado.</small></div>
      </div>

      <div className="ev-typebar">
        <span className="ev-type"><Lock size={16} />{/* BACKEND_GISS: event_type <- backend.incident.event_type */}Tipo de incidente actual: <b>{eventLabel(ev.event_type)}</b></span>
        <span className={`ev-badge ev-t-${state.c}`}><sv.Icon size={12} /> {state.t}</span>
      </div>

      <div className={`ev-cmd ev-t-${state.c}`}>
        <div className="ev-cmd-h"><Lock size={15} /><b>{/* BACKEND_GISS: action_type <- backend.response_action.action_type */}{atRisk ? "Comando intentado" : "Comando defensivo"}: {actionLabel(r.action_type)}</b>
          <span className="mu">{/* BACKEND_GISS: tool <- backend.response_action.tool */}{r.tool ? `Herramienta: ${r.tool}` : ""}{r.action_type ? ` · ${r.action_type}` : ""}</span></div>
        {lines.length ? (
          <div className="ev-term mono" role="log" aria-label="Terminal del comando defensivo" tabIndex={0}>
            {lines.map((l, i) => l.kind === "blank" ? <div key={i} className="gap" /> : (
              <div key={i}>{/* BACKEND_GISS: terminal_lines[i] <- backend.evidence.terminal_lines[i] {kind, timestamp, level, text} */}
                {l.timestamp && <span className="mu">[{hms(l.timestamp)}] </span>}
                {l.kind === "command" ? <span className="cmd">{l.text}</span> : <>{l.level && <span className={`lv ${levelClass(l.level)}`}>[{l.level}] </span>}<span>{l.text}</span></>}
              </div>))}
          </div>
        ) : preview ? (
          <div className="ev-term mono"><div><span className="mu">Comando previsto (aún no ejecutado):</span></div><div>{/* BACKEND_GISS: command_preview <- backend.response_action.command_preview */}<span className="cmd">{preview}</span></div></div>
        ) : <div className="ev-empty mu">El backend no entregó un comando defensivo para este incidente.</div>}
        {atRisk && (
          <div className="ev-errbox" role="alert"><AlertTriangle size={16} /><div><b>Error (sanitizado)</b><span>{/* BACKEND_GISS: failure_reason <- backend.response_action.failure_reason (sanitizado) */}{r.failure_reason ?? "El backend no entregó el motivo del fallo."}</span></div></div>
        )}
      </div>

      <div className="ev-reason">
        <h3><Info size={16} /> Motivo de esta respuesta</h3>
        <p>{/* BACKEND_GISS: reason <- backend.response_action.reason */}{r.reason ?? "Sin motivo registrado."}</p>
      </div>

      <div className="ev-tools">
        <h3><Terminal size={16} /> Herramientas utilizadas</h3><small className="mu">Tecnologías que participan en la detección y respuesta.</small>
        <div className="ev-toolgrid">
          {ev.tools.map((t, i) => { const I = TOOL_ICON[i % TOOL_ICON.length]; return (
            <div key={t.name}><I size={20} /><b>{t.name}</b><small className="mu">{t.detail}</small><small className="mu">({t.role})</small></div>); })}
        </div>
      </div>
    </section>
  );
}
