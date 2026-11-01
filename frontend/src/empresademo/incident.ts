/* Estado de incidente de EmpresaDemo (laboratorio). Todo es SIMULADO: no ejecuta scripts ni llama al backend.
   Textos y bloqueos tomados de la matriz de láminas 08-16 (handoff 18). CONTAINED nunca sale de un temporizador:
   solo existe por confirmación manual (Rama A); la contención real requiere señal validada + verificación técnica del backend. */

export type Phase = "NORMAL" | "DETECTED" | "LOCKDOWN" | "RESPONDING" | "CONTAINED" | "FAILED";
export type ModuleId = "accesos" | "clientes" | "documentos" | "reportes" | "administracion" | "perfil";
export type ActionId =
  | "login" | "changePassword" | "edit" | "replace" | "delete" | "bulkUpload"
  | "export" | "download" | "share" | "managePermissions" | "configure";

interface Rule { blocked: ActionId[]; restored: ActionId[] }

export interface Scenario extends Rule {
  id: string;
  num: number;            // número de lámina (08-13)
  title: string;
  script: string;         // nombre ilustrativo del script de la lámina (NO se ejecuta)
  module: ModuleId;       // módulo afectado
  alsoIn?: ModuleId[];    // otros módulos con las mismas reglas (ej. Login + Perfil)
  cross?: { module: ModuleId } & Rule; // recurso transversal (lámina 14: Clientes)
  detected: string; locked: string; measure: string; contained: string; failed: string;
  canEscalate: boolean;   // permite lockdown global (solo ante propagación de alto impacto confirmada)
}

const CLIENTS_CROSS: { module: ModuleId } & Rule = { module: "clientes", blocked: ["edit", "delete", "export"], restored: ["edit", "export"] };

export const SCENARIOS: Scenario[] = [
  { id: "brute_force", num: 8, title: "Intentos repetidos de acceso", script: "brute_force_demo.py", module: "accesos",
    detected: "Actividad anómala detectada en el acceso.",
    locked: "Acceso restringido mientras CyberShield verifica la actividad.",
    measure: "Medida EN CURSO: bloquear origen; restringir sesión afectada, si existe. Sin lockdown global si no entró.",
    contained: "Origen sospechoso bloqueado. El acceso legítimo continúa disponible.",
    failed: "No fue posible contener el acceso. Se requiere intervención. El acceso sensible permanece restringido.",
    blocked: ["login"], restored: ["login"], canEscalate: false },
  { id: "ransomware", num: 9, title: "Modificación anómala de documentos", script: "ransomware_demo.py", module: "documentos",
    detected: "Actividad de modificación anómala detectada.",
    locked: "Documentos sensibles en SOLO LECTURA.",
    measure: "Medida EN CURSO: solo lectura en sensibles; aislar módulo. Global solo por propagación confirmada.",
    contained: "Cambios no autorizados contenidos. Documentos protegidos.",
    failed: "Módulo AISLADO. Edición bloqueada. Intervención requerida.",
    blocked: ["edit", "replace", "delete", "bulkUpload"], restored: ["edit", "replace"], canEscalate: true },
  { id: "lateral_movement", num: 10, title: "Avance hacia recursos internos", script: "lateral_movement_demo.py", module: "administracion",
    detected: "Intento de acceso no autorizado a área crítica.",
    locked: "Acceso cerrado por CyberShield.",
    measure: "Medida EN CURSO: cerrar ruta, revocar sesión y aislar módulo o host. Mantener bloqueos.",
    contained: "Ruta de acceso restringida y sesión protegida.",
    failed: "Área crítica cerrada. Escalamiento al ingeniero requerido.",
    blocked: ["managePermissions", "configure"], restored: [], canEscalate: true },
  { id: "exfiltration", num: 11, title: "Salida inusual de información", script: "exfiltration_demo.py", module: "reportes", cross: CLIENTS_CROSS,
    detected: "Transferencia inusual detectada.",
    locked: "Salida de información restringida temporalmente.",
    measure: "Medida EN CURSO: restringir salida sospechosa; mantener consulta legítima. Mantener bloqueos.",
    contained: "Flujo sospechoso restringido. Reportes protegidos.",
    failed: "La salida permanece bloqueada. Intervención requerida.",
    blocked: ["export", "download", "share"], restored: ["export", "download", "share"], canEscalate: false },
  { id: "no_role", num: 12, title: "Rol sin autorización", script: "access_control_demo.py", module: "administracion",
    detected: "Intento de acceso no autorizado a área crítica.",
    locked: "Acceso cerrado por CyberShield.",
    measure: "Medida EN CURSO: cerrar acceso, marcar sesión y proteger el módulo. Mantener bloqueos.",
    contained: "Ruta de acceso restringida y sesión protegida. No cambia permisos ni concede acceso.",
    failed: "Módulo cerrado. Intervención del ingeniero requerida.",
    blocked: ["managePermissions", "configure"], restored: [], canEscalate: false },
  { id: "credential_abuse", num: 13, title: "Uso anómalo de credenciales", script: "credential_abuse_demo.py", module: "perfil", alsoIn: ["accesos"], cross: CLIENTS_CROSS,
    detected: "Actividad anómala detectada en el acceso · No reconocido.",
    locked: "Acceso restringido mientras CyberShield verifica la actividad.",
    measure: "Medida EN CURSO: revocar o cerrar la sesión comprometida y solicitar reautenticación legítima. Mantener bloqueos.",
    contained: "Sesión comprometida cerrada. Reautenticar al usuario legítimo; no se reactiva la sesión revocada.",
    failed: "Cuenta y sesión restringidas. Intervención del ingeniero requerida.",
    blocked: ["login", "changePassword"], restored: ["login"], canEscalate: false },
];

/** Lámina 16: lo que bloquea el LOCKDOWN GLOBAL. */
export const GLOBAL_BLOCKED: ActionId[] = ["edit", "delete", "export", "share", "managePermissions"];

export const ACTION_LABEL: Record<ActionId, string> = {
  login: "Iniciar sesión", changePassword: "Cambiar contraseña", edit: "Editar", replace: "Reemplazar",
  delete: "Eliminar", bulkUpload: "Carga masiva", export: "Exportar", download: "Descargar",
  share: "Compartir", managePermissions: "Administrar permisos", configure: "Configurar",
};

export const PHASE_LABEL: Record<Phase, string> = {
  NORMAL: "NORMAL", DETECTED: "DETECTED", LOCKDOWN: "LOCKDOWN",
  RESPONDING: "RESPONDING", CONTAINED: "CONTAINED", FAILED: "FAILED / ESCALATED",
};
export const PHASE_TONE: Record<Phase, string> = { NORMAL: "", DETECTED: "warn", LOCKDOWN: "bad", RESPONDING: "info", CONTAINED: "ok", FAILED: "bad" };

type Active = Exclude<Phase, "NORMAL">;
const RESPONDING_MSG = "CyberShield verifica que la actividad se detuvo.";
const CONTAINED_NOTE = "Contención confirmada · ilustración del estado posterior a una confirmación técnica; no es un hecho real.";
const FAILED_NOTE = "Intervención del ingeniero requerida. Sin reapertura automática.";

/** Lámina 14: Clientes protege sin perder contexto (recurso transversal). */
export const CLIENT_MSG: Record<Active, string> = {
  DETECTED: "CyberShield detectó actividad sospechosa. Consultas masivas señaladas; la consulta se conserva y no se afirma contención.",
  LOCKDOWN: "Acciones sensibles restringidas. Editar, Eliminar y Exportar deshabilitadas; Ver detalle y consulta permanecen disponibles.",
  RESPONDING: "CyberShield verifica que la actividad se detuvo. Medida EN CURSO: restringir consultas masivas de la sesión afectada. Se mantiene solo lectura.",
  CONTAINED: "Datos protegidos. Tras confirmación técnica se restauran gradualmente edición y exportación autorizadas; Eliminar requiere validación de rol.",
  FAILED: "Protección reforzada activa. Intervención del ingeniero requerida: solo lectura y exportación bloqueada; sin reapertura automática.",
};
/** Lámina 16: mensajes del lockdown global. */
export const GLOBAL_MSG: Record<Active, string> = {
  DETECTED: "CyberShield detectó actividad sospechosa.",
  LOCKDOWN: "Modo contención activo · CyberShield restringió temporalmente funciones sensibles para impedir que la actividad no autorizada avance.",
  RESPONDING: RESPONDING_MSG,
  CONTAINED: "Contención confirmada · Recuperación gradual.",
  FAILED: "Intervención del ingeniero requerida.",
};

export const findScenario = (id: string | null) => SCENARIOS.find((s) => s.id === id) ?? null;

/** ¿Cómo toca este escenario a un módulo? primary = su módulo (o alsoIn); cross = recurso transversal (Clientes). */
export function affects(sc: Scenario, module: ModuleId): "primary" | "cross" | null {
  if (sc.module === module || sc.alsoIn?.includes(module)) return "primary";
  return sc.cross?.module === module ? "cross" : null;
}

export function bannerText(sc: Scenario, phase: Active, module: ModuleId): { head: string; detail?: string } {
  const kind = affects(sc, module);
  if (kind === "cross") return { head: CLIENT_MSG[phase] };
  if (!kind) return { head: GLOBAL_MSG[phase] };
  switch (phase) {
    case "DETECTED": return { head: sc.detected, detail: "Resaltar el afectado; la consulta se conserva. No se afirma éxito." };
    case "LOCKDOWN": return { head: sc.locked };
    case "RESPONDING": return { head: RESPONDING_MSG, detail: sc.measure };
    case "CONTAINED": return { head: sc.contained, detail: CONTAINED_NOTE };
    case "FAILED": return { head: sc.failed, detail: FAILED_NOTE };
  }
}

export interface IncidentState { scenarioId: string | null; phase: Phase; global: boolean }
export const INITIAL_INCIDENT: IncidentState = { scenarioId: null, phase: "NORMAL", global: false };

export type IncidentEvent =
  | { type: "start"; id: string }          // NORMAL → DETECTED
  | { type: "advance" }                    // DETECTED → LOCKDOWN → RESPONDING
  | { type: "resolve"; branch: "A" | "B" } // RESPONDING → CONTAINED (A, confirmada) | FAILED (B, verificación fallida)
  | { type: "escalate" }                   // lockdown global (solo escenarios con canEscalate)
  | { type: "reset" };

export function incidentReducer(s: IncidentState, e: IncidentEvent): IncidentState {
  switch (e.type) {
    case "start":
      return findScenario(e.id) ? { scenarioId: e.id, phase: "DETECTED", global: false } : s;
    case "advance":
      if (s.phase === "DETECTED") return { ...s, phase: "LOCKDOWN" };
      if (s.phase === "LOCKDOWN") return { ...s, phase: "RESPONDING" };
      return s;
    case "resolve":
      return s.phase === "RESPONDING" ? { ...s, phase: e.branch === "A" ? "CONTAINED" : "FAILED" } : s;
    case "escalate": {
      const sc = findScenario(s.scenarioId);
      if (!sc?.canEscalate || s.phase === "NORMAL" || s.phase === "CONTAINED") return s;
      return { ...s, global: true, phase: s.phase === "DETECTED" ? "LOCKDOWN" : s.phase };
    }
    case "reset":
      return INITIAL_INCIDENT;
  }
}

/** ¿Está bloqueada esta acción en este módulo, dado el estado actual? DETECTED solo señala: no contiene. */
export function isLocked(s: IncidentState, action: ActionId, module: ModuleId): boolean {
  const sc = findScenario(s.scenarioId);
  if (!sc || s.phase === "NORMAL" || s.phase === "DETECTED") return false;
  if (s.global && s.phase !== "CONTAINED" && GLOBAL_BLOCKED.includes(action)) return true;
  const kind = affects(sc, module);
  if (!kind) return false; // el resto de módulos sigue operando por rol
  const rule: Rule = kind === "cross" ? sc.cross! : sc;
  if (s.phase === "CONTAINED") return rule.blocked.includes(action) && !rule.restored.includes(action);
  return rule.blocked.includes(action); // LOCKDOWN, RESPONDING y FAILED
}
