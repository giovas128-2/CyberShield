import { AlertTriangle, Check, Clock, Copy, Download, FileText, Info, ShieldCheck, Smartphone, Terminal } from "lucide-react";
import { useState } from "react";
import { SeverityBadge } from "../SeverityBadge";
import type { EvidenceView } from "../../types/evidenceView";
import { STEP_VISUAL, VERIFICATION_LABEL, buildTimeline, dateTime, eventLabel, evidenceAsText, hms, isAtRisk, levelClass, mmss, notificationVisual, statusVisual, ymd } from "./evidenceUtils";

/* Pantalla 1 · Detección y contención. Todo sale de `ev` (props); no hay datos fijos de un incidente concreto.
   Textos/colores/íconos de estado: salen de STATUS_VISUAL / STEP_VISUAL (evidenceUtils.ts), no de este archivo. */
export function DetectionPanel({ ev }: { ev: EvidenceView }) {
  const [copied, setCopied] = useState(false);
  const { steps, elapsed } = buildTimeline(ev);
  const sv = statusVisual(ev.status);
  const failed = ev.status === "FAILED", escalated = ev.status === "ESCALATED", contained = ev.status === "CONTAINED";
  const atRisk = isAtRisk(ev); // D3: FAILED/ESCALATED => la empresa sigue en riesgo (nunca "empresa protegida")
  const nv = notificationVisual(ev.response.notification, atRisk);
  const verified = ev.verification_result === "contained";

  const copyId = async () => { try { await navigator.clipboard.writeText(ev.incident_id); setCopied(true); setTimeout(() => setCopied(false), 1500); } catch { /* sin portapapeles: no pasa nada */ } };
  const download = () => { // Solo cliente: genera un .txt local, sin red.
    const url = URL.createObjectURL(new Blob([evidenceAsText(ev)], { type: "text/plain;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = `evidencia-${ev.incident_id}.txt`; a.click(); URL.revokeObjectURL(url);
  };

  return (
    <section className="card ev-pane" aria-labelledby="ev-p1">
      <div className="ev-head">
        <span className="ev-ico"><ShieldCheck size={22} /></span>
        <div><h2 id="ev-p1">Pantalla 1 · Detección y contención</h2><small className="mu">Flujo de detección del ataque y evidencia de la contención.</small></div>
        <span className="ev-tag">BACKEND REAL · evidencia verificada</span>
      </div>

      {ev.scenario_note && <div className="ev-note" role="note"><Info size={16} />{/* BACKEND_GISS: scenario_note <- backend.incident.simulation_note (opcional) */}<span>{ev.scenario_note}</span></div>}

      <div className="ev-sum">
        <div><small>ID DE INCIDENTE</small><b className="mono ev-id">{/* BACKEND_GISS: incident_id <- backend.incident.id */}{ev.incident_id}
          <button className="ev-icon" onClick={copyId} aria-label="Copiar ID del incidente">{copied ? <Check size={14} /> : <Copy size={14} />}</button></b></div>
        <div><small>ESTADO</small><span className={`ev-state ev-t-${sv.tone}`}>{/* BACKEND_GISS: status <- backend.evidence.status (DETECTED|RESPONDING|CONTAINED|FAILED|ESCALATED) */}<sv.Icon size={12} /> {sv.label}</span></div>
        <div><small>TIPO DE EVENTO</small><b>{/* BACKEND_GISS: event_type <- backend.incident.event_type */}{eventLabel(ev.event_type)}</b><small className="mu mono">{ev.event_type}</small></div>
        <div><small>SERVIDOR AFECTADO</small><b className="mono">{/* BACKEND_GISS: server <- backend.incident.server_name */}{ev.server ?? "—"}</b></div>
        <div><small>MITRE ATT&amp;CK</small>{ev.mitre_id
          ? <><b>{/* BACKEND_GISS: mitre_id / mitre_name <- backend.incident.mitre[0].technique_id / technique_name */}{ev.mitre_id}{ev.mitre_name ? ` - ${ev.mitre_name}` : ""}</b>{ev.mitre_tactic && <small className="mu">Táctica: {/* BACKEND_GISS: mitre_tactic <- backend.incident.mitre[0].tactic */}{ev.mitre_tactic}</small>}</>
          : <span className="mu">Sin clasificación MITRE confirmada</span>}</div>
        <div><small>SEVERIDAD</small>{/* BACKEND_GISS: severity <- backend.incident.severity */}<SeverityBadge value={ev.severity} /></div>
        <div><small>IP DE ORIGEN</small><b className="mono">{/* BACKEND_GISS: source_ip <- backend.event.source_ip */}{ev.source_ip ?? "—"}</b></div>
        <div><small>REGLA APLICADA</small><b className="mono">{/* BACKEND_GISS: rule <- backend.evidence.rule */}{ev.rule ?? "—"}</b></div>
        <div><small>DETECTADO</small><b>{/* BACKEND_GISS: detected_at <- backend.incident.detected_at (ISO 8601 UTC) */}{dateTime(ev.detected_at)}</b></div>
        <div><small>VERIFICACIÓN</small>{/* BACKEND_GISS: verification_result <- backend.response_action.verification_result (contained|failed|null) */}
          {ev.verification_result ? <b className={`ev-t-${ev.verification_result === "contained" ? "ok" : "er"}`}>{VERIFICATION_LABEL[ev.verification_result]}</b> : <span className="mu">Pendiente</span>}</div>
      </div>

      <div className="ev-box">
        <div className="ev-head slim">
          <span className="ev-ico sm"><Terminal size={16} /></span>
          <div><h3>Consola de evidencia</h3><small className="mu">Registro de eventos y acciones ejecutadas por CyberShield.</small></div>
          <button className="ab" onClick={download} disabled={!ev.entries.length}><Download size={14} />Descargar evidencia</button>
        </div>
        {ev.entries.length ? (
          <div className="ev-log mono" role="log" aria-label="Consola de evidencia" tabIndex={0}>
            {ev.entries.map((e, i) => (
              <div key={i}>{/* BACKEND_GISS: entries[i] <- backend.evidence[i] {timestamp, level, source, message} */}
                <span className="mu">[{ymd(e.timestamp)} {hms(e.timestamp)}]</span> <span className={`lv ${levelClass(e.level)}`}>[{e.level}]</span> <span>{e.source}: {e.message}</span></div>))}
          </div>
        ) : <div className="ev-empty mu">Sin registros de evidencia para este incidente.</div>}
      </div>

      <div className="ev-box">
        <div className="ev-head slim">
          <span className="ev-ico sm"><Clock size={16} /></span>
          <div><h3>Línea de tiempo del incidente</h3><small className="mu">Proceso de detección y contención.</small></div>
          <span className="ev-elapsed" title="Calculado con los timestamps de la evidencia">Tiempo transcurrido {/* BACKEND_GISS: elapsed_time <- calculado con entries[].timestamp / response_finished_at (respaldo: backend.elapsed_time) */}<b className="mono">{elapsed != null ? mmss(elapsed) : "--:--"}</b></span>
        </div>
        <ol className="ev-tl" aria-label="Línea de tiempo">
          {steps.map((s) => { const v = STEP_VISUAL[s.state]; const tone = s.final && s.state === "done" ? "ok" : v.tone; return (
            <li key={s.key + s.label} className={`st-${s.state}${tone ? ` tone-${tone}` : ""}`}>{/* BACKEND_GISS: círculo <- entries[].stage + entries[].timestamp (y verification_result para el último) */}
              <span className="dot">{v.Icon ? <v.Icon size={16} /> : null}</span>
              <b className="mono">{s.offset}</b><span>{s.label}</span>
              <small className="sr">{v.sr}</small>
            </li>); })}
        </ol>
      </div>

      {contained && verified && ev.outcomes.length > 0 && (
        <div className="ev-result ev-t-ok" role="status">
          <h3><Check size={16} /> Resultado de la contención</h3>
          <div className="ev-outs">{ev.outcomes.map((o) => <div key={o.label}><Check size={14} /><div><b>{o.label}</b><small className="mu">{o.detail}</small></div></div>)}</div>
        </div>
      )}
      {contained && verified && ev.outcomes.length === 0 && <div className="ev-result ev-t-ok" role="status"><h3><Check size={16} /> Ataque contenido</h3></div>}
      {contained && !verified && <div className="ev-result ev-t-wn" role="status"><h3><Clock size={16} /> Contención sin verificar</h3><p>El backend marca el incidente como contenido pero no entregó verification_result=contained; no se muestra "empresa protegida".</p></div>}
      {atRisk && (
        <div className={`ev-result ev-fail ev-t-${sv.tone}`} role="alert">
          <h3><AlertTriangle size={18} /> {failed ? "Respuesta fallida / intervención requerida" : "Incidente escalado / intervención requerida"}</h3>
          <p className="ev-risk"><b>La empresa sigue en riesgo</b> hasta que un ingeniero aplique la contención manualmente.</p>
          <dl className="ev-fail-d">
            <dt>Motivo del fallo</dt><dd>{/* BACKEND_GISS: failure_reason <- backend.response_action.failure_reason (sanitizado) */}{ev.response.failure_reason ?? "El backend no entregó el motivo del fallo."}</dd>
            <dt>Acción intentada</dt><dd className="mono">{/* BACKEND_GISS: action_type <- backend.response_action.action_type */}{ev.response.action_type ?? "—"}</dd>
          </dl>
        </div>
      )}
      {ev.status === "RESPONDING" && <div className={`ev-result ev-t-${sv.tone}`} role="status"><h3><Clock size={16} /> Respuesta en curso…</h3><p>Aún no hay verificación de contención. "Acción ejecutada" y "Ataque bloqueado" siguen en gris hasta que el backend lo confirme.</p></div>}
      {ev.status === "DETECTED" && <div className={`ev-result ev-t-${sv.tone}`} role="status"><h3><FileText size={16} /> Incidente detectado</h3><p>Todavía no se inicia la respuesta.</p></div>}
      {nv && ev.response.notification && (
        <div className={`ev-notif ev-t-${nv.tone}`} role="status">{/* BACKEND_GISS: notification <- backend.notification {channel,status,notified}. El texto "Ingeniero notificado" solo sale si notified=true */}
          <Smartphone size={18} /><div><b>{nv.title}</b><small>Notificación móvil: {ev.response.notification.channel} · {ev.response.notification.status}</small></div></div>
      )}
      {atRisk && !ev.response.notification && <div className="ev-notif ev-t-wn" role="status"><Smartphone size={18} /><div><b>Sin dato de notificación móvil</b><small>{/* BACKEND_GISS: notification <- backend.notification (no llegó) */}El backend no informó si se avisó al ingeniero; confirmar manualmente.</small></div></div>}
    </section>
  );
}
