import type {
  EvidenceEntry,
  EvidenceStage,
  EvidenceStatus,
  EvidenceView,
  LogLevel,
  TerminalLine,
  VerificationResult,
} from "../../types/evidenceView";


type Obj = Record<string, unknown>;


const isObj = (
  value: unknown
): value is Obj =>
  typeof value === "object"
  && value !== null
  && !Array.isArray(value);


const str = (
  value: unknown
): string | null =>
  typeof value === "string"
  && value.trim() !== ""
    ? value
    : null;


const numberValue = (
  value: unknown
): number | null =>
  typeof value === "number"
  && Number.isFinite(value)
    ? value
    : null;


function incidentCode(
  value: unknown
): string | null {
  if (
    typeof value === "number"
    && Number.isFinite(value)
  ) {
    return `INC-${String(value).padStart(3, "0")}`;
  }

  if (typeof value === "string") {
    const clean = value.trim();

    if (!clean) return null;

    if (
      clean
        .toUpperCase()
        .startsWith("INC-")
    ) {
      return clean.toUpperCase();
    }

    const numeric = Number(clean);

    if (Number.isFinite(numeric)) {
      return `INC-${String(numeric).padStart(3, "0")}`;
    }
  }

  return null;
}


function normalizeStatus(
  value: unknown
): EvidenceStatus {
  const raw = String(
    value ?? ""
  ).toUpperCase();

  if (
    raw === "DETECTED"
    || raw === "RESPONDING"
    || raw === "CONTAINED"
    || raw === "FAILED"
    || raw === "ESCALATED"
  ) {
    return raw as EvidenceStatus;
  }

  return "DETECTED";
}


function normalizeSeverity(
  value: unknown
):
  | "NORMAL"
  | "WARNING"
  | "HIGH"
  | "CRITICAL" {
  const raw = String(
    value ?? ""
  ).toUpperCase();

  if (
    raw === "WARNING"
    || raw === "HIGH"
    || raw === "CRITICAL"
  ) {
    return raw;
  }

  return "NORMAL";
}


function normalizeStage(
  value: unknown
): EvidenceStage | null {
  const raw = String(
    value ?? ""
  ).toUpperCase();

  const allowed: EvidenceStage[] = [
    "ATTACK_RECEIVED",
    "DETECTED",
    "RULE_APPLIED",
    "INCIDENT_CREATED",
    "RESPONDING",
    "CONTAINED",
    "FAILED",
    "ESCALATED",
  ];

  return allowed.includes(
    raw as EvidenceStage
  )
    ? raw as EvidenceStage
    : null;
}


function logLevelForStage(
  stage: EvidenceStage
): LogLevel {
  switch (stage) {
    case "CONTAINED":
      return "OK";

    case "FAILED":
      return "ERROR";

    case "ESCALATED":
      return "WARN";

    case "RESPONDING":
      return "INFO";

    default:
      return "INFO";
  }
}


function stageMessage(
  stage: EvidenceStage,
  response: Obj
): string {
  switch (stage) {
    case "DETECTED":
      return "CyberShield detectó y registró el incidente.";

    case "RESPONDING":
      return str(
        response.action_type
      )
        ? `CyberShield inició ${response.action_type}.`
        : "CyberShield inició una respuesta defensiva.";

    case "CONTAINED":
      return "La respuesta defensiva fue verificada y el ataque quedó contenido.";

    case "FAILED":
      return "La respuesta defensiva no logró contener el incidente.";

    case "ESCALATED":
      return "El incidente requiere intervención del ingeniero.";

    default:
      return stage;
  }
}


function buildEntries(
  raw: Obj,
  incidentId: string,
  response: Obj
): EvidenceEntry[] {
  const timeline = Array.isArray(
    raw.timeline
  )
    ? raw.timeline
    : [];

  const entries: EvidenceEntry[] = [];

  for (const item of timeline) {
    if (!isObj(item)) continue;

    const stage = normalizeStage(
      item.stage
    );

    if (!stage) continue;

    const timestamp =
      str(item.timestamp) ?? "";

    const completed =
      typeof item.completed === "boolean"
        ? item.completed
        : false;

    entries.push({
      incident_id: incidentId,
      event_id:
        typeof raw.event_id === "number"
        || typeof raw.event_id === "string"
          ? raw.event_id
          : null,

      stage,
      timestamp,

      source:
        str(raw.source)
        ?? "CyberShield",

      level:
        logLevelForStage(stage),

      message:
        stageMessage(
          stage,
          response
        ),

      action_type:
        str(response.action_type),

      command_display: null,

      result:
        stage === "CONTAINED"
          ? str(response.result)
          : null,

      success:
        stage === "CONTAINED"
          ? true
          : stage === "FAILED"
          ? false
          : completed
          ? true
          : null,
    });
  }

  return entries;
}


function buildTerminalLines(
  response: Obj
): TerminalLine[] {

  /*
    OLA 4:
    Si el backend ya entrega terminal_lines,
    usamos esa evidencia real directamente.
  */

  if (
    Array.isArray(
      response.terminal_lines
    )
  ) {
    const backendLines:
      TerminalLine[] = [];

    for (
      const item
      of response.terminal_lines
    ) {
      if (!isObj(item)) {
        continue;
      }

      const kindRaw =
        String(
          item.kind ?? ""
        ).toLowerCase();

      const levelRaw =
        String(
          item.level ?? "INFO"
        ).toUpperCase();

      const textValue =
        str(item.text);

      if (!textValue) {
        continue;
      }

      const kind =
        kindRaw === "command"
        || kindRaw === "output"
        || kindRaw === "blank"
          ? kindRaw
          : "output";

      const level =
        levelRaw === "OK"
        || levelRaw === "WARN"
        || levelRaw === "ERROR"
        || levelRaw === "INFO"
          ? levelRaw
          : "INFO";

      backendLines.push({
        kind,
        level,
        text: textValue,
      });
    }

    if (backendLines.length > 0) {
      return backendLines;
    }
  }

  /*
    Compatibilidad con evidencia histórica:
    si el backend viejo no tiene terminal_lines,
    seguimos mostrando response.result.
  */

  const result = str(
    response.result
  );

  const lines: TerminalLine[] =
    [];

  if (result) {
    const parts = result.split(
      "\n"
    );

    for (const part of parts) {
      const trimmed =
        part.trim();

      if (!trimmed) {
        continue;
      }

      const rollback =
        trimmed.startsWith(
          "ROLLBACK:"
        );

      lines.push({
        kind: "output",
        level:
          rollback
            ? "INFO"
            : "OK",
        text: trimmed,
      });
    }
  }

  return lines;
}


function verificationFrom(
  status: EvidenceStatus,
  response: Obj
): VerificationResult {
  const responseStatus = String(
    response.status ?? ""
  ).toLowerCase();

  if (
    status === "FAILED"
    || responseStatus === "failed"
  ) {
    return "failed";
  }

  if (
    status === "CONTAINED"
    || responseStatus === "executed"
    || responseStatus === "rolled_back"
  ) {
    return "contained";
  }

  return null;
}


export function adaptEvidencePayload(
  raw: unknown
): EvidenceView | null {
  if (!isObj(raw)) {
    return null;
  }

  const incidentId = incidentCode(
    raw.incident_id
  );

  if (!incidentId) {
    return null;
  }


  const detection = isObj(
    raw.detection
  )
    ? raw.detection
    : {};


  const mitre = isObj(
    raw.mitre
  )
    ? raw.mitre
    : {};


  const response = isObj(
    raw.response
  )
    ? raw.response
    : {};


  const status = normalizeStatus(
    raw.status
  );


  const verification =
    verificationFrom(
      status,
      response
    );


  const entries =
    buildEntries(
      raw,
      incidentId,
      response
    );


  const terminalLines =
    buildTerminalLines(
      response
    );


  const actionType =
    str(response.action_type);


  const source =
    str(raw.source)
    ?? "CyberShield";


  const tools: EvidenceView["tools"] =
    [];


  if (
    source.toLowerCase()
      === "wazuh"
  ) {
    tools.push({
      name: "Wazuh",
      detail:
        "Detección y correlación del evento.",
      role: "Sensor / HIDS",
    });
  }


  if (
    source.toLowerCase()
      === "suricata"
  ) {
    tools.push({
      name: "Suricata",
      detail:
        "Telemetría y análisis de tráfico.",
      role: "IDS / NSM",
    });
  }


  if (actionType) {
    tools.push({
      name: "CyberShield",
      detail:
        `Orquestación de ${actionType}.`,
      role: "Respuesta defensiva",
    });
  }


  const outcomes:
    EvidenceView["outcomes"] =
    verification === "contained"
      ? [
          {
            label:
              "Respuesta defensiva verificada",
            detail:
              str(response.result)
              ?? "CyberShield confirmó la contención.",
          },
        ]
      : [];


  const createdAt =
    str(response.created_at);

  const executedAt =
    str(response.executed_at);

  const rolledBackAt =
    str(response.rolled_back_at);


  return {
    incident_id: incidentId,

    event_id:
      typeof raw.event_id === "number"
      || typeof raw.event_id === "string"
        ? raw.event_id
        : null,

    event_type:
      str(raw.event_type)
      ?? "unknown",

    severity:
      normalizeSeverity(
        raw.severity
      ),

    status,

    server:
      numberValue(
        raw.server_id
      ) !== null
        ? `Servidor #${raw.server_id}`
        : null,

    scenario_note:
      null,

    source_ip:
      str(raw.source_ip),

    rule:
      str(detection.rule_id),

    mitre_id:
      str(
        mitre.technique_id
      ),

    mitre_name:
      str(
        mitre.technique_name
      ),

    mitre_tactic:
      str(
        mitre.tactic
      ),

    detected_at:
      str(
        detection.timestamp
      )
      ?? (
        entries.find(
          (entry) =>
            entry.stage ===
            "DETECTED"
        )?.timestamp
        ?? null
      ),

    response_started_at:
      createdAt,

    response_finished_at:
      rolledBackAt
      ?? executedAt,

    elapsed_time:
      null,

    verification_result:
      verification,

    entries,

    response: {
      action_type:
        actionType,

      tool:
        str(response.tool)
        ?? (
          source.toLowerCase()
            === "wazuh"
            ? "Wazuh / CyberShield"
            : source.toLowerCase()
              === "suricata"
              ? "Suricata / CyberShield"
              : "CyberShield"
        ),

      command_display:
        str(
          response.command_display
        ),

      command_preview:
        str(
          response.command_display
        ),

      terminal_lines:
        terminalLines,

      reason:
        str(response.reason),

      result:
        str(response.result),

      success:
        verification
          === "contained"
          ? true
          : verification
            === "failed"
            ? false
            : null,

      failure_reason:
        str(
          response.failure_reason
        ),

      /*
        Telegram/notificación real se
        conectará después.
      */
      notification:
        null,
    },

    outcomes,

    tools,
  };
}
