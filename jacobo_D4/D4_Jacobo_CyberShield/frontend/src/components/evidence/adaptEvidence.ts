import type { EvidenceEntry, EvidenceStage, EvidenceStatus, IncidentEvidence, LogLevel, TerminalLine, VerificationResult } from "../../types/evidence";

/* ÚNICO punto de entrada del JSON real. BACKEND_GISS: cuando exista el endpoint, haz
   `const ev = adaptEvidencePayload(await respuestaJson)` y pásalo a <DetectionPanel ev={ev} /> / <DefensiveCommandPanel ev={ev} />.
   Si el JSON real nombra distinto algún campo, se corrige AQUÍ (una sola función) y no en los componentes.
   Es defensivo: nunca lanza excepción; devuelve null si el payload no trae ni incident_id (la pantalla muestra "Sin evidencia"). */

const STAGES: EvidenceStage[] = ["ATTACK_RECEIVED", "DETECTED", "RULE_APPLIED", "INCIDENT_CREATED", "RESPONDING", "CONTAINED", "FAILED", "ESCALATED"];
const STATUSES: EvidenceStatus[] = ["DETECTED", "RESPONDING", "CONTAINED", "FAILED", "ESCALATED"];
const LEVELS: LogLevel[] = ["INFO", "OK", "WARN", "DENIED", "ERROR"];
const SEVERITIES = ["NORMAL", "WARNING", "HIGH", "CRITICAL"] as const;

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => typeof v === "object" && v !== null && !Array.isArray(v);
const str = (v: unknown): string | null => (typeof v === "string" && v.trim() !== "" ? v : null);
const numOrNull = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const boolOrNull = (v: unknown): boolean | null => (typeof v === "boolean" ? v : null);
const arr = (v: unknown): unknown[] => (Array.isArray(v) ? v : []);
const oneOf = <T extends string>(v: unknown, list: readonly T[]): T | null => (typeof v === "string" && (list as readonly string[]).includes(v) ? (v as T) : null);

function adaptEntry(raw: unknown, incidentId: string): EvidenceEntry | null {
  if (!isObj(raw)) return null;
  const stage = oneOf(raw.stage, STAGES);
  if (!stage) return null;   // sin stage conocido no se puede ubicar en el timeline
  return {
    incident_id: str(raw.incident_id) ?? incidentId,
    event_id: typeof raw.event_id === "number" || typeof raw.event_id === "string" ? raw.event_id : null,
    stage,
    timestamp: str(raw.timestamp) ?? "",   // "" => se muestra "—" y NO colorea el círculo
    source: str(raw.source) ?? "—",
    level: oneOf(raw.level, LEVELS) ?? "INFO",
    message: str(raw.message) ?? "",
    action_type: str(raw.action_type),
    command_display: str(raw.command_display),
    result: str(raw.result),
    success: boolOrNull(raw.success),
  };
}

function adaptLine(raw: unknown): TerminalLine | null {
  if (!isObj(raw)) return null;
  const kind = oneOf(raw.kind, ["command", "output", "blank"] as const);
  if (!kind) return null;
  return { kind, timestamp: str(raw.timestamp) ?? undefined, level: oneOf(raw.level, LEVELS) ?? undefined, text: typeof raw.text === "string" ? raw.text : "" };
}

/* Si el backend no manda status válido, se deduce de lo que sí llegó (no se inventa un éxito). */
function deriveStatus(entries: EvidenceEntry[], verification: VerificationResult): EvidenceStatus {
  if (entries.some((e) => e.stage === "ESCALATED")) return "ESCALATED";
  if (entries.some((e) => e.stage === "FAILED") || verification === "failed") return "FAILED";
  if (verification === "contained") return "CONTAINED";
  if (entries.some((e) => e.stage === "RESPONDING")) return "RESPONDING";
  return "DETECTED";
}

export function adaptEvidencePayload(raw: unknown): IncidentEvidence | null {
  if (!isObj(raw)) return null;
  const incident_id = str(raw.incident_id);
  if (!incident_id) return null;
  const entries = arr(raw.entries).map((e) => adaptEntry(e, incident_id)).filter((e): e is EvidenceEntry => e !== null);
  const r = isObj(raw.response) ? raw.response : {};
  const verification: VerificationResult = raw.verification_result === "contained" || raw.verification_result === "failed" ? raw.verification_result : null;
  const notif = isObj(r.notification) && str(r.notification.channel) ? { channel: str(r.notification.channel)!, status: str(r.notification.status) ?? "—", notified: boolOrNull(r.notification.notified) } : null; // BACKEND_GISS: notification.notified <- backend.notification.sent (bool)
  return {
    incident_id,
    event_id: typeof raw.event_id === "number" || typeof raw.event_id === "string" ? raw.event_id : null,
    event_type: str(raw.event_type) ?? "desconocido",
    severity: oneOf(raw.severity, SEVERITIES) ?? "NORMAL",
    status: oneOf(raw.status, STATUSES) ?? deriveStatus(entries, verification),
    server: str(raw.server),
    scenario_note: str(raw.scenario_note), // BACKEND_GISS: scenario_note <- backend.incident.simulation_note (opcional)
    source_ip: str(raw.source_ip),
    rule: str(raw.rule),
    mitre_id: str(raw.mitre_id),
    mitre_name: str(raw.mitre_name),
    mitre_tactic: str(raw.mitre_tactic),
    detected_at: str(raw.detected_at),
    response_started_at: str(raw.response_started_at),
    response_finished_at: str(raw.response_finished_at),
    elapsed_time: numOrNull(raw.elapsed_time),
    verification_result: verification,
    entries,
    response: {
      action_type: str(r.action_type),
      tool: str(r.tool),
      command_display: str(r.command_display),
      command_preview: str(r.command_preview) ?? str(r.command_display), // BACKEND_GISS: command_preview <- backend.response_action.command_preview (si no existe se usa command_display)
      terminal_lines: arr(r.terminal_lines).map(adaptLine).filter((l): l is TerminalLine => l !== null),
      reason: str(r.reason),
      result: str(r.result),
      success: boolOrNull(r.success),
      failure_reason: str(r.failure_reason),
      notification: notif,
    },
    outcomes: arr(raw.outcomes).filter(isObj).map((o) => ({ label: str(o.label) ?? "", detail: str(o.detail) ?? "" })).filter((o) => o.label),
    tools: arr(raw.tools).filter(isObj).map((t) => ({ name: str(t.name) ?? "", detail: str(t.detail) ?? "", role: str(t.role) ?? "" })).filter((t) => t.name),
  };
}
