import { AlertTriangle, Check, Clock, FileText, X, type LucideIcon } from "lucide-react";
import type { EvidenceEntry, EvidenceStage, EvidenceStatus, EvidenceView, LogLevel } from "../../types/evidenceView";

/* Tono = clase CSS (.t-in / .t-wn / .t-ok / .t-er). Los colores viven en styles.css; aquí solo se elige el tono. */
export type Tone = "in" | "wn" | "ok" | "er";

/* UNA sola tabla de estado -> texto / tono / ícono. Los componentes no escriben textos ni colores de estado por su cuenta. */
export const STATUS_VISUAL: Record<EvidenceStatus, { label: string; responseLabel: string; tone: Tone; Icon: LucideIcon; risk: boolean }> = {
  DETECTED: { label: "Detectado", responseLabel: "Sin respuesta aún", tone: "in", Icon: FileText, risk: false },
  RESPONDING: { label: "Respondiendo", responseLabel: "Respuesta en curso", tone: "wn", Icon: Clock, risk: false },
  CONTAINED: { label: "Contenido", responseLabel: "Respuesta ejecutada", tone: "ok", Icon: Check, risk: false },
  FAILED: { label: "Respuesta fallida", responseLabel: "Respuesta fallida · intervención requerida", tone: "er", Icon: X, risk: true },
  ESCALATED: { label: "Escalado", responseLabel: "Escalado · intervención requerida", tone: "wn", Icon: AlertTriangle, risk: true },
};
export const statusVisual = (s: EvidenceStatus) => STATUS_VISUAL[s] ?? STATUS_VISUAL.DETECTED;

/* Estado de cada círculo -> ícono / tono. futuro (pending) = gris sin ícono, en curso (active) = gris con pulso. */
export type StepKind = "done" | "active" | "failed" | "escalated" | "pending";
export const STEP_VISUAL: Record<StepKind, { Icon: LucideIcon | null; tone: Tone | null; sr: string }> = {
  done: { Icon: Check, tone: "in", sr: "completado" },
  active: { Icon: null, tone: null, sr: "en curso" },
  failed: { Icon: X, tone: "er", sr: "fallido" },
  escalated: { Icon: AlertTriangle, tone: "wn", sr: "escalado" },
  pending: { Icon: null, tone: null, sr: "pendiente" },
};

/* Etiquetas SOLO de presentación (no son datos del backend). */
export const TIMELINE_STEPS: { key: EvidenceStage; label: string }[] = [
  { key: "ATTACK_RECEIVED", label: "Ataque recibido" },
  { key: "DETECTED", label: "Evento detectado" },
  { key: "RULE_APPLIED", label: "Regla aplicada" },
  { key: "INCIDENT_CREATED", label: "Incidente creado" },
  { key: "RESPONDING", label: "Acción ejecutada" },
  { key: "CONTAINED", label: "Ataque bloqueado" },
];
/* ESCALATED primero: si hay FAILED y luego ESCALATED, el estado final es el escalamiento. */
const TERMINAL_FAIL: EvidenceStage[] = ["ESCALATED", "FAILED"];
/* Texto del último círculo cuando la respuesta no se logró (nunca verde). */
const FAIL_LABEL: Record<"FAILED" | "ESCALATED", string> = { FAILED: "Respuesta fallida / intervención requerida", ESCALATED: "Escalado / intervención requerida" };

/* Etiqueta legible del tipo de evento; si no se conoce, se muestra el valor crudo (no se inventa). */
/* Etiquetas SOLO de presentación: si un event_type/action_type no está aquí, se muestra el valor crudo. Agregar un ataque nuevo = una línea, sin tocar los componentes.
   (Nombres tomados del diagrama de flujo del documento: fuerza bruta, abuso de privilegios, ransomware-like, exfiltración, movimiento lateral.) */
const EVENT_LABEL: Record<string, string> = {
  multiple_login_attempts: "Fuerza bruta", privilege_escalation: "Escalación de privilegios", critical_file_change: "Cambio sospechoso de archivo",
  ransomware_like_behavior: "Comportamiento compatible con ransomware", data_exfiltration: "Posible exfiltración de datos", lateral_movement: "Movimiento lateral",
};
export const eventLabel = (t: string) => EVENT_LABEL[t] ?? t.replaceAll("_", " ");
const ACTION_LABEL: Record<string, string> = {
  BLOCK_SOURCE_IP: "Bloqueo de IP de origen", REVOKE_SESSION: "Revocación de sesión", BLOCK_ACCOUNT: "Bloqueo de cuenta",
  STOP_PROCESS: "Detener proceso sospechoso", CONTAIN_HOST: "Contención del host", RESTRICT_DATA_FLOW: "Restricción de flujo de datos", RESTRICT_LATERAL: "Restricción de comunicación lateral",
};
export const actionLabel = (a: string | null) => (a ? ACTION_LABEL[a] ?? a : "Sin acción registrada");
export const VERIFICATION_LABEL = { contained: "Contenido (verificado)", failed: "Falló la verificación" } as const;

const ms = (iso: string | null | undefined) => { const t = iso ? Date.parse(iso) : NaN; return Number.isNaN(t) ? null : t; };
export const hms = (iso: string | null | undefined) => { const t = ms(iso); return t == null ? "—" : new Date(t).toISOString().slice(11, 19); };
export const ymd = (iso: string | null | undefined) => { const t = ms(iso); return t == null ? "—" : new Date(t).toISOString().slice(0, 10); };
export const dateTime = (iso: string | null | undefined) => {
  const t = ms(iso); if (t == null) return "—";
  const d = new Date(t); const m = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"][d.getUTCMonth()];
  return `${d.getUTCDate()} ${m} ${d.getUTCFullYear()}, ${d.toISOString().slice(11, 16)} UTC`;
};
export const mmss = (sec: number) => `${String(Math.floor(sec / 60)).padStart(2, "0")}:${String(Math.round(sec % 60)).padStart(2, "0")}`;

export interface StepState { key: EvidenceStage; label: string; state: StepKind; final: boolean; at: string | null; offset: string }

/* Reglas del timeline (todo sale de ev.entries / verification_result, nada fijo):
   · Círculos 1-4: completados solo si existe una entrada con ese stage Y timestamp válido; si no, grises.
   · Círculo 5 "Acción ejecutada": completado solo cuando una entrada RESPONDING trae success=true (o la respuesta terminó en FAILED/ESCALATED
     tras haberse intentado). Con la respuesta aún en curso queda gris con pulso ("en curso").
   · Círculo 6 "Ataque bloqueado": verde SOLO si hay entrada CONTAINED con timestamp Y verification_result === "contained".
     Si llega FAILED/ESCALATED pasa a rojo/ámbar (nunca verde). */
export function buildTimeline(ev: EvidenceView): { steps: StepState[]; elapsed: number | null } {
  const stamps = ev.entries.map((e) => ms(e.timestamp)).filter((x): x is number => x != null);
  const t0 = stamps.length ? Math.min(...stamps) : null;
  const first = (k: EvidenceStage, pred: (e: EvidenceEntry) => boolean = () => true) => ev.entries.find((e) => e.stage === k && ms(e.timestamp) != null && pred(e))?.timestamp ?? null;
  const failStage = TERMINAL_FAIL.find((k) => first(k));
  const off = (iso: string | null) => { const t = ms(iso); return t != null && t0 != null ? mmss((t - t0) / 1000) : "--:--"; };

  const steps = TIMELINE_STEPS.map((s, i): StepState => {
    const last = i === TIMELINE_STEPS.length - 1;
    if (last) {
      if (failStage) return { key: failStage, label: FAIL_LABEL[failStage as "FAILED" | "ESCALATED"], state: failStage === "FAILED" ? "failed" : "escalated", final: true, at: first(failStage), offset: off(first(failStage)) };
      const okAt = ev.verification_result === "contained" ? first("CONTAINED") : null;
      return { key: s.key, label: s.label, state: okAt ? "done" : "pending", final: true, at: okAt, offset: off(okAt) };
    }
    if (s.key === "RESPONDING") {
      const executed = first("RESPONDING", (e) => e.success === true);
      const attempted = first("RESPONDING");
      /* D3: si la respuesta terminó en FAILED/ESCALATED y NUNCA hubo un RESPONDING con success=true, la acción se intentó pero no se ejecutó bien:
         el círculo 5 queda en rojo ("fallido") y el timeline se detiene ahí. Si sí hubo éxito y falló la verificación, el 5 queda completo y falla el 6. */
      if (!executed && failStage && attempted) return { key: s.key, label: s.label, state: "failed", final: false, at: attempted, offset: off(attempted) };
      return { key: s.key, label: s.label, state: executed ? "done" : attempted ? "active" : "pending", final: false, at: executed, offset: off(executed) }; // en curso => --:-- (aún no hay hora de "ejecutada")
    }
    const stamp = first(s.key);
    return { key: s.key, label: s.label, state: stamp ? "done" : "pending", final: false, at: stamp, offset: off(stamp) };
  });

  /* Tiempo transcurrido REAL: del primer timestamp al fin de la respuesta (response_finished_at) o, si aún no termina, al último evento recibido.
     Solo si no hay timestamps utilizables se usa ev.elapsed_time del backend. BACKEND_GISS: elapsed_time <- backend.elapsed_time (respaldo) */
  const end = ms(ev.response_finished_at) ?? (stamps.length ? Math.max(...stamps) : null);
  const computed = t0 != null && end != null && end >= t0 && stamps.length > 1 ? (end - t0) / 1000 : null;
  return { steps, elapsed: computed ?? ev.elapsed_time };
}

export const levelClass = (l: LogLevel | undefined) => (l === "OK" ? "ok" : l === "WARN" ? "wn" : l === "DENIED" || l === "ERROR" ? "er" : "in");

/* Texto plano descargable (solo cliente; no hay llamada de red). */
export function evidenceAsText(ev: EvidenceView): string {
  const head = [`Evidencia ${ev.incident_id} · ${ev.event_type} · estado ${ev.status}`, `Origen: ${ev.source_ip ?? "—"} · Servidor: ${ev.server ?? "—"}`, ""];
  return head.concat(ev.entries.map((e: EvidenceEntry) => `[${e.timestamp || "—"}] [${e.level}] ${e.source}: ${e.message}`)).join("\n") + "\n";
}

/* D3: la empresa sigue en riesgo mientras la respuesta no se logró (FAILED/ESCALATED). Nunca se muestra "empresa protegida" en este caso. */
export const isAtRisk = (ev: EvidenceView) => statusVisual(ev.status).risk;
/* Texto del aviso móvil según lo que diga el backend (notified): no se afirma "notificado" si el backend no lo confirma. */
export function notificationVisual(n: EvidenceView["response"]["notification"], atRisk = false): { title: string; tone: Tone } | null {
  if (!n) return null;
  if (n.notified === true) return { title: atRisk ? "Ingeniero notificado" : "Notificación móvil enviada", tone: "ok" }; // "Ingeniero notificado" solo en FAILED/ESCALATED
  if (n.notified === false) return { title: "Ingeniero NO notificado", tone: "er" };
  return { title: "Notificación móvil", tone: "in" };
}
