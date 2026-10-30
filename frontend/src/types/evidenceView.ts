/* Contrato visual de "Evidencia de protección / Respuesta real" (D3).
   Campos tomados del Plan Maestro (D1 Sebas/César): incident_id, event_id, stage, timestamp, source, message,
   action_type, command_display, result y success. 07_evidence_payload_example.json no venía en lo adjuntado:
   si el JSON real difiere, solo se ajusta src/components/evidence/adaptEvidence.ts (+ el mock y MAPEO_BACKEND_FRONTEND.md).
   D2: se agregan mitre_id/mitre_name/mitre_tactic planos, response_started_at, response_finished_at,
   elapsed_time y verification_result.
   D3: response.command_preview (reemplaza al comando escrito en el front), response.notification.notified, scenario_note
   (aviso de simulación controlada) y el soporte genérico de FAILED/ESCALATED y de varios event_type/action_type con el MISMO componente. */

/* Estados del incidente (Plan: DETECTED -> RESPONDING -> CONTAINED | FAILED | ESCALATED). */
export type EvidenceStatus = "DETECTED" | "RESPONDING" | "CONTAINED" | "FAILED" | "ESCALATED";
/* Etapas que alimentan los 6 círculos del timeline. */
export type EvidenceStage = "ATTACK_RECEIVED" | "DETECTED" | "RULE_APPLIED" | "INCIDENT_CREATED" | "RESPONDING" | "CONTAINED" | "FAILED" | "ESCALATED";
export type LogLevel = "INFO" | "OK" | "WARN" | "DENIED" | "ERROR";
/* Resultado de la verificación posterior a la respuesta. null = aún no hay verificación. */
export type VerificationResult = "contained" | "failed" | null;

export interface EvidenceEntry {
  incident_id: string;
  event_id: number | string | null;
  stage: EvidenceStage;
  timestamp: string;               // ISO 8601 (UTC)
  source: string;                  // Suricata | Wazuh | CyberShield | Firewall ...
  level: LogLevel;
  message: string;
  action_type: string | null;
  command_display: string | null;
  result: string | null;
  success: boolean | null;
}

export interface TerminalLine {
  kind: "command" | "output" | "blank";
  timestamp?: string;              // ISO 8601
  level?: LogLevel;                // se muestra como [OK] / [DENIED] ...
  text: string;
}

export interface EvidenceTool { name: string; detail: string; role: string }
export interface EvidenceOutcome { label: string; detail: string }

export interface EvidenceView {
  incident_id: string;
  event_id: number | string | null;
  event_type: string;              // multiple_login_attempts, ...
  severity: "NORMAL" | "WARNING" | "HIGH" | "CRITICAL";
  status: EvidenceStatus;
  server: string | null;
  scenario_note: string | null;    // D3: aviso opcional (p. ej. "simulación controlada / comportamiento compatible con ransomware")
  source_ip: string | null;
  rule: string | null;
  mitre_id: string | null;         // T1110. Si es null => "Sin clasificación MITRE confirmada"
  mitre_name: string | null;       // Brute Force
  mitre_tactic: string | null;     // Credential Access
  detected_at: string | null;      // ISO 8601
  response_started_at: string | null;   // ISO 8601; null = la respuesta aún no inicia
  response_finished_at: string | null;  // ISO 8601; null = la respuesta aún no termina
  elapsed_time: number | null;     // segundos entregados por el backend (opcional). La pantalla prefiere calcularlo con timestamps.
  verification_result: VerificationResult;
  entries: EvidenceEntry[];
  response: {
    action_type: string | null;
    tool: string | null;
    command_display: string | null;
    command_preview: string | null; // D3: comando (o vista previa) que entrega el backend para ESTE incidente. El front no trae comandos propios.
    terminal_lines: TerminalLine[];
    reason: string | null;
    result: string | null;
    success: boolean | null;
    failure_reason: string | null; // ya sanitizado por el backend
    notification: { channel: string; status: string; notified: boolean | null } | null; // notified: true = el ingeniero ya fue avisado; null = el backend no lo dice
  };
  outcomes: EvidenceOutcome[];
  tools: EvidenceTool[];
}

/* Escenarios del MOCK (solo desarrollo). El estado real lo dicta el backend; esto solo permite recorrer los 3 estados. */
export type EvidenceScenario = "detected" | "responding" | "contained" | "failed" | "escalated";
/* Ataque del MOCK (solo desarrollo). Con backend real lo dicta event_type; la pantalla es la misma para todos. */
export type EvidenceAttack = "brute_force" | "ransomware";

/* Lo que la pantalla sabe pintar: cargando / listo / sin evidencia / error de API. */
export type EvidenceResult =
  | { phase: "loading" }
  | { phase: "ready"; ev: EvidenceView }
  | { phase: "empty"; incident_id: string }
  | { phase: "error"; code: string; message: string };
