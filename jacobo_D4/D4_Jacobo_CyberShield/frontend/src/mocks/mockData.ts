/* ============================================================================================================
   MOCK CENTRAL ÚNICO de CyberShield (frontend desacoplado · D4)          >>> DATOS DE DEMOSTRACIÓN, NO REALES <<<
   TODOS los datos de ejemplo de la aplicación viven SOLO en este archivo. Ningún componente trae datos propios.
   Este archivo NO hace fetch / axios / WebSocket y no conoce ninguna URL ni endpoint.

   Cómo lo usa la app:  componentes -> src/api/client.ts (funciones getXxx) -> este archivo.
   Giss: para conectar el backend se reemplaza el CUERPO de cada función de src/api/client.ts (ver README_INTEGRACION_GISS.md)
   y este archivo puede quedarse como fixture de desarrollo o borrarse.

   Convención de comentarios:   BACKEND_GISS: <variable visual> <- <dato backend esperado>
   Buscar todos los puntos de conexión:   grep -rn BACKEND_GISS src
   ============================================================================================================ */
import type { ActionItem, Device, EventStats, Evento, Incidente, LabScenario, MitreTechnique, NotificationItem, Protection, ServerItem, SessionItem, Stats, User } from "../types";
import type { EvidenceAttack, EvidenceEntry, EvidenceScenario, EvidenceStage, LogLevel, TerminalLine } from "../types/evidence";

const ago = (minutes: number) => new Date(Date.now() - minutes * 60000).toISOString();

/* ---------- 1. Usuario de la sesión (login / registro) ---------- */
/* BACKEND_GISS: user.id <- backend.user.id · user.name <- backend.user.name · user.email <- backend.user.email */
export const MOCK_USER: User = { id: 1, name: "Analista Demo", email: "analista@cybershield.demo" };

/* ---------- 2. Servidores ---------- */
/* BACKEND_GISS: ServerItem.id <- server.id · name <- server.name · ipAddress <- server.ip_address · status <- server.status (online|offline|registered)
   · agent <- server.agent · createdAt <- server.created_at · lastSeen <- server.last_seen */
export const MOCK_SERVERS: ServerItem[] = [
  { id: 1, name: "srv-prod-01", ipAddress: "192.168.56.10", status: "online", agent: "Wazuh 4.x", createdAt: ago(60 * 24 * 12), lastSeen: ago(1) },
  { id: 2, name: "srv-cyber-01", ipAddress: "192.168.56.20", status: "online", agent: "Wazuh 4.x + Suricata", createdAt: ago(60 * 24 * 12), lastSeen: ago(1) },
  { id: 3, name: "srv-files-01", ipAddress: "192.168.56.30", status: "online", agent: "Wazuh 4.x (FIM)", createdAt: ago(60 * 24 * 9), lastSeen: ago(2) },
  { id: 4, name: "srv-backup-01", ipAddress: "192.168.56.40", status: "offline", agent: null, createdAt: ago(60 * 24 * 5), lastSeen: ago(60 * 26) },
];

/* ---------- 3. Eventos ---------- */
/* BACKEND_GISS: Evento.id <- event.id · createdAt <- event.created_at (ISO UTC) · fecha <- se calcula de created_at · tipo <- event.event_type
   · origen <- event.source_ip · severidad <- event.severity · estado <- event.estado (o se deduce de severity) · scope <- event.scope (BLOCKED|REACHED|IMPACT)
   · serverId <- event.server_id · serverName <- event.server_name */


export const MOCK_EVENTS: Evento[] = [
  { id: 1, fecha: "12:01", createdAt: ago(8), tipo: "authentication_failure", origen: "192.168.1.10", severidad: "NORMAL", estado: "Registrado", scope: "BLOCKED", serverId: 2 },
  { id: 2, fecha: "12:03", createdAt: ago(6), tipo: "authentication_burst", origen: "192.168.1.50", severidad: "HIGH", estado: "Detectado", scope: "REACHED", serverId: 2 },
  { id: 3, fecha: "12:04", createdAt: ago(4), tipo: "suspicious_network_traffic", origen: "192.168.1.80", severidad: "WARNING", estado: "Registrado", scope: "REACHED", serverId: 2 },
  { id: 4, fecha: "12:05", createdAt: ago(2), tipo: "privilege_escalation", origen: "192.168.1.90", severidad: "CRITICAL", estado: "Detectado", scope: "IMPACT", serverId: 2 },
  { id: 5, fecha: "15:00", createdAt: ago(30), tipo: "multiple_login_attempts", origen: "192.168.56.50", severidad: "HIGH", estado: "Detectado", scope: "BLOCKED", serverId: 1, serverName: "srv-prod-01" },
  { id: 6, fecha: "16:30", createdAt: ago(20), tipo: "ransomware_like_behavior", origen: "192.168.56.30", severidad: "CRITICAL", estado: "Detectado", scope: "IMPACT", serverId: 3, serverName: "srv-files-01" },
];

export const MOCK_INC_SEED: Incidente[] = [
  {
    id: "INC-003", backendId: 3, eventType: "authentication_burst",
    titulo: "Patrón sospechoso de autenticación",
    resumen: "Actividad de autenticación contra varias cuentas en una ventana corta.",
    severidad: "HIGH", estado: "Investigando", status: "investigating",
    origen: "192.168.1.50", servidor: "srv-cyber-01", servicio: "Autenticación",
    detectado: "14 oct 2026 · 12:03", asignado: "César", regla: "AUTH-CORRELATION",
    reco: "Validar el origen, las cuentas afectadas y si hubo acceso exitoso posterior.",
    investigationSteps: ["Revisar origen y cuentas afectadas.", "Correlacionar fallos y accesos exitosos.", "Buscar actividad privilegiada posterior."],
    mitre: [],
    resolutionCriteria: "La actividad quedó explicada o contenida con evidencia suficiente.",
  },
];


/* ---------- 4. Incidentes ---------- */
/* BACKEND_GISS: Incidente.backendId <- incident.id · id (INC-007) <- se arma con incidentCode(incident.id) · eventId <- incident.event_id
   · eventType <- incident.event_type · titulo/resumen/servicio/regla <- se derivan de event_type (client.ts) o de incident.title/summary si el backend los trae
   · severidad <- incident.severity · status <- incident.status (open|investigating|resolved) · estado <- texto de status
   · origen <- incident.source_ip · servidor <- incident.server_name · detectado <- incident.created_at · asignado <- incident.assigned_to
   · reco <- incident.recommendation · investigationSteps <- incident.investigation_steps[] · resolutionCriteria <- incident.resolution_criteria
   · mitre[] <- incident.mitre_techniques[] {technique_id, technique_name, tactic, reference_url, is_primary, notes}
   · responseAction <- incident.response_action {id, action_type, target, status, reversible, duration_seconds, reason, result, created_at, executed_at, rolled_back_at} */
const mitreBF: MitreTechnique[] = [{ technique_id: "T1110", technique_name: "Brute Force", tactic: "Credential Access", url: "https://attack.mitre.org/techniques/T1110/", is_primary: true, rationale: "Múltiples intentos de autenticación contra el mismo servicio." }];
const mitreRW: MitreTechnique[] = [{ technique_id: "T1486", technique_name: "Data Encrypted for Impact", tactic: "Impact", url: "https://attack.mitre.org/techniques/T1486/", is_primary: true, rationale: "Modificación masiva de archivos compatible con cifrado (simulación controlada)." }];

export const MOCK_INCIDENTS: Incidente[] = [
  {
    id: "INC-077", backendId: 77, eventId: 5, eventType: "multiple_login_attempts",
    titulo: "Múltiples intentos de autenticación",
    resumen: "Se detectaron varios intentos de autenticación SSH en una ventana corta desde un mismo origen.",
    severidad: "HIGH", estado: "Pendiente", status: "open",
    origen: "192.168.56.50", servidor: "srv-prod-01", servicio: "Autenticación",
    detectado: "27 oct 2026 · 15:00", asignado: "—", regla: "CYBERSHIELD-RULE",
    reco: "Bloquear la IP de origen y validar que no hubo acceso exitoso posterior.",
    investigationSteps: ["Revisar el origen y las cuentas afectadas.", "Confirmar que la IP quedó bloqueada en el firewall.", "Buscar accesos exitosos posteriores."],
    mitre: mitreBF,
    resolutionCriteria: "La IP de origen quedó bloqueada y no hay nuevos intentos.",
    responseAction: { id: 1, action_type: "BLOCK_SOURCE_IP", target: "192.168.56.50", status: "executed", reversible: true, duration_seconds: 7200, reason: "Fuerza bruta (T1110) → bloquear IP de origen", result: "contained", created_at: ago(30), executed_at: ago(29), rolled_back_at: null },
  },
  {
    id: "INC-078", backendId: 78, eventId: 6, eventType: "ransomware_like_behavior",
    titulo: "Comportamiento compatible con ransomware (simulación)",
    resumen: "Simulación controlada: modificación masiva de archivos en el servidor de archivos. No es malware real.",
    severidad: "CRITICAL", estado: "Investigando", status: "investigating",
    origen: "192.168.56.30", servidor: "srv-files-01", servicio: "Sistema de archivos",
    detectado: "28 oct 2026 · 16:30", asignado: "Analista Demo", regla: "CYBERSHIELD-RULE-RANSOM-SIM",
    reco: "Detener el proceso sospechoso, aislar el host y validar la integridad de los archivos.",
    investigationSteps: ["Identificar el proceso que modifica archivos.", "Aislar el host de la red de producción.", "Validar la integridad de los archivos con la copia de respaldo."],
    mitre: mitreRW,
    resolutionCriteria: "El proceso fue detenido y no hay nuevas modificaciones masivas de archivos.",
    responseAction: { id: 2, action_type: "STOP_PROCESS", target: "srv-files-01", status: "failed", reversible: true, duration_seconds: null, reason: "Comportamiento compatible con ransomware (T1486) → detener proceso", result: "failed", created_at: ago(20), executed_at: null, rolled_back_at: null },
  },
  ...MOCK_INC_SEED,
];

/* ---------- 5. Resumen del dashboard (los totales se recalculan en useCyberShieldData a partir de las listas) ---------- */
/* BACKEND_GISS: Stats.servidores <- summary.servers · servidoresOnline <- summary.servers_online · servidoresOffline <- summary.servers_offline
   · eventos <- summary.events · incidentes <- summary.incidents · criticos <- summary.critical_incidents · estado <- texto del dashboard */
export const MOCK_DASHBOARD: Stats = { estado: "Monitoreo activo. Revisa los incidentes y eventos recientes.", servidores: 4, servidoresOnline: 3, servidoresOffline: 1, eventos: 6, incidentes: 3, criticos: 1 };

/* ---------- 6. Estadísticas de eventos por ventana (1 s / 60 s) ---------- */
/* BACKEND_GISS: EventStats.total_events <- stats.total_events · by_source[] <- stats.by_source [{source_ip,count}] · by_type[] <- stats.by_type [{event_type,count}]
   · by_scope <- stats.by_scope {BLOCKED,REACHED,IMPACT} · by_server[] <- stats.by_server [{server_id,count}] · window_seconds <- stats.window_seconds */
export const MOCK_EVENT_STATS: Record<"1s" | "60s", EventStats> = {
  "1s": { window: "1s", window_seconds: 1, total_events: 1, by_source: [{ source_ip: "192.168.1.90", count: 1 }], by_type: [{ event_type: "privilege_escalation", count: 1 }], by_scope: { BLOCKED: 0, REACHED: 0, IMPACT: 1 }, by_server: [{ server_id: 2, count: 1 }] },
  "60s": { window: "60s", window_seconds: 60, total_events: 6, by_source: [{ source_ip: "192.168.56.50", count: 2 }, { source_ip: "192.168.1.50", count: 2 }, { source_ip: "192.168.1.90", count: 1 }, { source_ip: "192.168.56.30", count: 1 }], by_type: [{ event_type: "authentication_burst", count: 2 }, { event_type: "multiple_login_attempts", count: 1 }, { event_type: "privilege_escalation", count: 1 }, { event_type: "ransomware_like_behavior", count: 1 }, { event_type: "authentication_failure", count: 1 }], by_scope: { BLOCKED: 2, REACHED: 3, IMPACT: 1 }, by_server: [{ server_id: 2, count: 4 }, { server_id: 1, count: 1 }, { server_id: 3, count: 1 }] },
};

/* ---------- 7. Notificaciones ---------- */
/* BACKEND_GISS: NotificationItem.id <- notification.id · incident_id <- notification.incident_id · severity <- notification.severity · recipient <- notification.recipient
   · channel <- notification.channel · message <- notification.message · status <- notification.status · created_at / sent_at <- notification.created_at / sent_at */
export const MOCK_NOTIFICATIONS: NotificationItem[] = [
  { id: 1, incident_id: 77, severity: "HIGH", recipient: "ingeniero.guardia", channel: "Telegram", message: "Fuerza bruta contenida: IP 192.168.56.50 bloqueada en srv-prod-01.", status: "sent", created_at: ago(29), sent_at: ago(29) },
  { id: 2, incident_id: 78, severity: "CRITICAL", recipient: "ingeniero.guardia", channel: "Telegram", message: "Respuesta fallida en srv-files-01: se requiere intervención manual.", status: "sent", created_at: ago(19), sent_at: ago(19) },
];

/* ---------- 8. Dispositivos, sesiones, acciones, protecciones y laboratorio ---------- */
/* BACKEND_GISS (todo este bloque): Device.* <- device.{id,device_name,user,platform,status,last_seen,source_mode} · SessionItem.* <- session.{id,user,device,ip,started_at,status,source_mode}
   · ActionItem.* <- response_action.{id,action_type,target,status,incident_id,created_at,reversible,source_mode} · Protection.* <- control.{id,name,sensor,description,source_mode,mitre_techniques}
   · LabScenario.* <- scenario.{id,name,control,description,event_source,source_mode,mitre_techniques} */
/* DATOS SIMULADOS de Dispositivos, Sesiones, Acciones, Protecciones y Laboratorio.
   Se reemplazan cuando exista el endpoint real (ver src/api/client.ts). Los mapeos MITRE son de demostración:
   deben ser revisados por el responsable de ciberseguridad antes de presentarse como reales. */

const mt = (id: string, name: string, tactic: string, primary = true): MitreTechnique => ({
  technique_id: id, technique_name: name, tactic, is_primary: primary,
  url: `https://attack.mitre.org/techniques/${id.replace(".", "/")}/`, rationale: "Asociación contextual de demostración; no confirma por sí sola un ataque.",
});

export const MOCK_DEVICES: Device[] = [
  { id: "dev-1", name: "laptop-ventas-01", user: "usuario.demo", os: "Windows 11", status: "trusted", last_seen: ago(3), mode: "simulated" },
  { id: "dev-2", name: "desconocido-10.20.4.19", user: null, os: "Windows", status: "unauthorized", last_seen: ago(12), mode: "simulated" },
  { id: "dev-3", name: "tablet-bodega", user: "bodega.demo", os: "Android", status: "unknown", last_seen: ago(180), mode: "simulated" },
];
export const MOCK_SESSIONS: SessionItem[] = [
  { id: "ses-1", user: "usuario.demo", device: "laptop-ventas-01", ip: "192.168.1.60", started_at: ago(12), status: "active", mode: "simulated" },
  { id: "ses-2", user: "admin.demo", device: "desconocido-10.20.4.19", ip: "10.20.4.19", started_at: ago(95), status: "revoked", mode: "simulated" },
];
export const MOCK_ACTIONS: ActionItem[] = [
  { id: "act-1", type: "Bloquear IP", target: "185.220.101.34", status: "executed", incident_id: 842, created_at: ago(2), reversible: true, mode: "simulated" },
  { id: "act-2", type: "Revocar sesión", target: "ses-2", status: "executed", incident_id: 839, created_at: ago(60), reversible: true, mode: "simulated" },
  { id: "act-3", type: "Aislar servidor", target: "srv-demo-03", status: "pending", incident_id: null, created_at: ago(5), reversible: true, mode: "simulated" },
];
export const MOCK_PROTECTIONS: Protection[] = [
  { id: "c1", name: "Fuerza bruta", sensor: "Wazuh", description: "Monitoreo con respuesta segura y reversible en el laboratorio.", mode: "integrated", mitre: [mt("T1110", "Brute Force", "Credential Access")] },
  { id: "c2", name: "Dispositivo no autorizado", sensor: "Aplicación", description: "Device Trust preparado; validación E2E con backend/BD pendiente.", mode: "pending", mitre: [mt("T1078", "Valid Accounts", "Defense Evasion")] },
  { id: "c3", name: "Cambio de archivo crítico", sensor: "Wazuh FIM", description: null, mode: "integrated", mitre: [mt("T1565.001", "Stored Data Manipulation", "Impact")] },
  { id: "c4", name: "Abuso de privilegios", sensor: "Wazuh", description: "Señal Wazuh disponible; cierre E2E real pendiente de adaptación del evento sudo.", mode: "pending", mitre: [mt("T1548.003", "Sudo and Sudo Caching", "Privilege Escalation")] },
  { id: "c5", name: "Conexión externa sospechosa", sensor: "Suricata", description: "Telemetría de red disponible; integración de la regla al backend pendiente.", mode: "pending", mitre: [mt("T1041", "Exfiltration Over C2 Channel", "Exfiltration")] },
  { id: "c6", name: "Posible exfiltración de datos", sensor: "Suricata + App", description: "Escenario defensivo con datos ficticios; no implica exfiltración confirmada.", mode: "simulated", mitre: [mt("T1041", "Exfiltration Over C2 Channel", "Exfiltration")] },
  { id: "c7", name: "Comportamiento tipo ransomware", sensor: "Wazuh", description: "Patrón benigno de modificaciones masivas; no utiliza malware ni cifrado real.", mode: "simulated", mitre: [mt("T1486", "Data Encrypted for Impact", "Impact")] },
  { id: "c8", name: "Posible movimiento lateral", sensor: "Wazuh + Suricata", description: "Conexión SSH autorizada entre hosts del laboratorio; clasificación contextual.", mode: "simulated", mitre: [mt("T1021.004", "Remote Services: SSH", "Lateral Movement")] },
];
export const MOCK_SCENARIOS: LabScenario[] = MOCK_PROTECTIONS.map((p, i) => ({
  id: `sc${i + 1}`, name: p.name, control: p.name, description: "Genera telemetría defensiva de prueba para validar detección, clasificación y respuesta.",
  event_source: p.sensor, mode: p.mode === "integrated" ? "integrated" : "simulated", mitre: p.mitre,
}));


/* ---------- 9. EmpresaDemo (aplicación corporativa FICTICIA protegida por CyberShield) ---------- */
/* BACKEND_GISS: ED_DEVICES[].trusted <- device_trust.trusted (decide si el equipo entra a /empresa-demo/inicio o a "acceso restringido")
   · ED_PROFILE.session <- session.id · ED_PROFILE.user/alias <- user.username/name · el resto (clientes, documentos, reportes) es contenido ficticio de la app demo, no viene de CyberShield. */
export const ED_DATE_LABEL = "Martes, 20 de octubre de 2026";
export const ED_ORIGIN = "ORIGEN: DEMO · 20 oct 2026 · 10:24 UTC";

export interface EDDevice { name: string; id: string; trusted: boolean }
export const ED_DEVICES: Record<string, EDDevice> = {
  "demo-equipo-01": { name: "demo-equipo-01", id: "DV-001", trusted: true },
  "demo-equipo-06": { name: "demo-equipo-06", id: "DV-006", trusted: false },
};
export const ED_PROFILE = { alias: "Analista Demo", user: "analista.demo", org: "Oficina central ficticia", role: "Analista de muestra", session: "SES-011" };

export interface EDClient { id: string; code: string; name: string; sector: string; owner: string; status: "En curso" | "En revisión" | "En seguimiento"; last: string; note: string }
export const ED_CLIENTS: EDClient[] = [
  { id: "c1", code: "CLI-001", name: "Proyecto Olivo", sector: "Servicios profesionales", owner: "Equipo Demo A", status: "En curso", last: "Hoy · Propuesta v3", note: "Relación activa desde septiembre de 2026. Propuesta comercial DOC-018 actualizada hoy a las 10:08. Próximo hito ficticio: revisión de alcance." },
  { id: "c2", code: "CLI-002", name: "Estudio Bruma", sector: "Diseño y consultoría", owner: "Equipo Demo B", status: "En curso", last: "Hoy · Resumen revisado", note: "Resumen de servicio DOC-016 revisado esta mañana. Sin pendientes críticos." },
  { id: "c3", code: "CLI-003", name: "Grupo Ladera", sector: "Operaciones", owner: "Equipo Demo A", status: "En revisión", last: "19 oct · Plan de trabajo", note: "Plan de trabajo DOC-012 en borrador, pendiente de revisión del equipo." },
  { id: "c4", code: "CLI-004", name: "Taller Marea", sector: "Producción", owner: "Equipo Demo C", status: "En curso", last: "18 oct · Entrega de muestra", note: "Entrega de muestra DOC-011 revisada." },
  { id: "c5", code: "CLI-005", name: "Casa Umbral", sector: "Comercio", owner: "Equipo Demo B", status: "En seguimiento", last: "17 oct · Nota de proyecto", note: "Nota de proyecto DOC-009 por revisar." },
  { id: "c6", code: "CLI-006", name: "Nodo Prado", sector: "Tecnología", owner: "Equipo Demo C", status: "En curso", last: "16 oct · Reporte mensual", note: "Reporte mensual compartido con el equipo." },
];

export interface EDDoc { id: string; code: string; title: string; kind: string; client: string; state: "Por revisar" | "Revisado" | "Borrador"; version: string; when: string; owner: string; outline: string[] }
export const ED_DOCS: EDDoc[] = [
  { id: "d1", code: "DOC-018", title: "Propuesta comercial", kind: "Documento", client: "Proyecto Olivo", state: "Por revisar", version: "v3", when: "Hoy · 10:08", owner: "Equipo Demo A", outline: ["Objetivo del proyecto", "Alcance orientativo", "Próximos pasos"] },
  { id: "d2", code: "DOC-016", title: "Resumen de servicio", kind: "Documento", client: "Estudio Bruma", state: "Revisado", version: "v2", when: "Hoy · 09:42", owner: "Equipo Demo B", outline: ["Contexto", "Servicios entregados", "Siguientes pasos"] },
  { id: "d3", code: "DOC-012", title: "Plan de trabajo", kind: "Documento", client: "Grupo Ladera", state: "Borrador", version: "v1", when: "Ayer", owner: "Equipo Demo A", outline: ["Etapas", "Responsables ficticios", "Calendario de muestra"] },
  { id: "d4", code: "DOC-011", title: "Entrega de muestra", kind: "Documento", client: "Taller Marea", state: "Revisado", version: "v2", when: "18 oct", owner: "Equipo Demo C", outline: ["Resumen", "Entregables", "Observaciones"] },
  { id: "d5", code: "DOC-009", title: "Nota de proyecto", kind: "Nota", client: "Casa Umbral", state: "Por revisar", version: "v1", when: "17 oct", owner: "Equipo Demo B", outline: ["Contexto", "Notas"] },
];

export const ED_ACTIVITY = [
  { t: "10:08", title: "Propuesta actualizada", meta: "DOC-018 · Proyecto Olivo · Versión 3" },
  { t: "09:42", title: "Documento revisado", meta: "DOC-016 · Estudio Bruma" },
  { t: "09:30", title: "Reporte consultado", meta: "REP-006 · Resumen de octubre" },
  { t: "09:00", title: "Acceso normal", meta: "Analista Demo · Equipo de confianza" },
];
export const ED_REPORTS = [
  { code: "REP-006", name: "Resumen de octubre", period: "Octubre 2026", content: "Actividad del equipo", last: "Hoy · 09:30" },
  { code: "REP-005", name: "Seguimiento documental", period: "Octubre 2026", content: "Versiones y revisiones", last: "19 oct · 15:20" },
  { code: "REP-004", name: "Panorama de clientes", period: "Septiembre 2026", content: "Relaciones y proyectos", last: "17 oct · 11:05" },
];
/* Distribución ilustrativa del 1 al 20 de octubre; no representa productividad real. */
export const ED_BARS = [5, 9, 6, 12, 8, 10, 19, 38, 15, 8, 6, 5];


/* ---------- 10. Evidencia de protección / respuesta real (pantallas 1 y 2) ---------- */
/* BACKEND_GISS: buildMockEvidencePayload() fabrica lo que devolvería el backend para un incidente. Giss NO lo llama: pide el JSON real
   y lo pasa por adaptEvidencePayload() (src/components/evidence/adaptEvidence.ts). Contrato completo en MAPEO_BACKEND_FRONTEND.md. */
type Notif = { channel: string; status: string; notified: boolean | null };
type Outcome = { label: string; detail: string };

/* Todo lo que cambia de un ataque a otro. La pantalla es la misma; solo cambian estos datos. */
interface AttackMock {
  day: string;            // BACKEND_GISS: entries[].timestamp <- backend.evidence[].timestamp (ISO 8601 UTC); aquí solo se arma el mock
  event_type: string;     // BACKEND_GISS: event_type <- backend.incident.event_type
  severity: "NORMAL" | "WARNING" | "HIGH" | "CRITICAL"; // BACKEND_GISS: severity <- backend.incident.severity
  server: string;         // BACKEND_GISS: server <- backend.incident.server_name
  source_ip: string | null; // BACKEND_GISS: source_ip <- backend.event.source_ip
  rule: string;           // BACKEND_GISS: rule <- backend.evidence.rule
  mitre_id: string; mitre_name: string; mitre_tactic: string; // BACKEND_GISS: mitre_* <- backend.incident.mitre[0].{technique_id,technique_name,tactic}
  action_type: string;    // BACKEND_GISS: response.action_type <- backend.response_action.action_type
  tool: string;           // BACKEND_GISS: response.tool <- backend.response_action.tool
  command_preview: string; // BACKEND_GISS: response.command_preview <- backend.response_action.command_preview  (Giss lo reemplaza con el comando real)
  scenario_note: string | null; // BACKEND_GISS: scenario_note <- backend.incident.simulation_note (opcional)
  reason: string;         // BACKEND_GISS: response.reason <- backend.response_action.reason
  actionVerb: string;     // texto de la entrada RESPONDING ("Bloqueo de IP (…)")
  failure_reason: string; // BACKEND_GISS: response.failure_reason <- backend.response_action.failure_reason (YA sanitizado por el backend)
  attack: [number, LogLevel, string, string][];  // [segundo, nivel, fuente, mensaje] de ATTACK_RECEIVED
  detect: [number, LogLevel, string, string][];  // idem para DETECTED
  applied: string[];      // líneas de salida (OK) cuando la acción se ejecuta bien
  verifyLines: [string, string];  // [intento de verificación, resultado de la verificación (DENIED/OK)]
  contained_msg: string;
  failed_line: string;    // salida de error de la terminal (mock; el backend la entrega en terminal_lines)
  outcomes: Outcome[];
  tools: { name: string; detail: string; role: string }[]; // BACKEND_GISS: tools[] <- backend.evidence.tools (o lista fija decidida por Giss)
}

const ATTACKS: Record<EvidenceAttack, AttackMock> = {
  brute_force: {
    day: "2026-10-27T15:00:",
    event_type: "multiple_login_attempts", severity: "HIGH", server: "srv-prod-01", source_ip: "192.168.56.50", rule: "CYBERSHIELD-RULE",
    mitre_id: "T1110", mitre_name: "Brute Force", mitre_tactic: "Credential Access",
    action_type: "BLOCK_SOURCE_IP", tool: "iptables / Wazuh Active Response",
    command_preview: "sudo iptables -I INPUT -s 192.168.56.50 -j DROP", // BACKEND_GISS: command_preview <- backend.response_action.command_preview
    scenario_note: null,
    reason: "El incidente actual corresponde a un ataque de fuerza bruta (MITRE T1110). Por ello, CyberShield muestra y ejecuta únicamente el comando defensivo asociado a este tipo de ataque, que consiste en bloquear la IP de origen en el firewall.",
    actionVerb: "Bloqueo de IP (192.168.56.50)",
    failure_reason: "El helper de Active Response no confirmó la regla (timeout). Requiere intervención manual.",
    attack: [[0, "INFO", "Suricata", "Intento de autenticación SSH detectado"], [1, "INFO", "Suricata", "IP origen: 192.168.56.50 -> Servidor: srv-prod-01 (SSH/22)"]],
    detect: [[2, "INFO", "Wazuh", "Múltiples intentos de autenticación (12 en 45s)"]],
    applied: ["Regla insertada correctamente.", "IP 192.168.56.50 bloqueada en firewall."],
    verifyLines: ["Nuevo intento de conexión SSH desde 192.168.56.50", "Conexión rechazada por firewall (DROP)."],
    contained_msg: "El ataque de fuerza bruta ha sido contenido.",
    failed_line: "No se pudo insertar la regla (tiempo de espera agotado).",
    outcomes: [
      { label: "Ataque contenido", detail: "No se detectan más intentos del origen en monitoreo." },
      { label: "Acceso denegado", detail: "La IP de origen fue bloqueada en firewall." },
      { label: "Proceso detenido", detail: "Intentos de conexión denegados." },
      { label: "Empresa protegida", detail: "Los sistemas continúan operativos." },
    ],
    tools: [
      { name: "Wazuh", detail: "Detección de eventos", role: "HIDS / NIDS" }, { name: "Suricata", detail: "Análisis de tráfico de red", role: "NIDS" },
      { name: "CyberShield Engine", detail: "Coordinación y respuesta automática", role: "Motor" }, { name: "PostgreSQL", detail: "Almacenamiento de eventos", role: "Base de datos" },
      { name: "Firewall / Active Response", detail: "Ejecución de comandos defensivos", role: "Respuesta" },
    ],
  },
  ransomware: {
    day: "2026-10-28T16:30:",
    event_type: "ransomware_like_behavior", severity: "CRITICAL", server: "srv-files-01", source_ip: "192.168.56.30", rule: "CYBERSHIELD-RULE-RANSOM-SIM",
    mitre_id: "T1486", mitre_name: "Data Encrypted for Impact", mitre_tactic: "Impact",
    action_type: "STOP_PROCESS", tool: "Wazuh Active Response / sistema operativo",
    command_preview: "[command_preview · lo entrega el backend para la acción STOP_PROCESS]", // BACKEND_GISS: command_preview <- backend.response_action.command_preview (placeholder: NO se inventa un comando)
    scenario_note: "Simulación controlada: comportamiento compatible con ransomware generado en el laboratorio. No es malware real.",
    reason: "El incidente actual muestra un comportamiento compatible con ransomware (MITRE T1486): modificación masiva de archivos. CyberShield muestra únicamente la acción defensiva asociada a este tipo de incidente: detener el proceso sospechoso y contener el host.",
    actionVerb: "Detener proceso sospechoso (srv-files-01)",
    failure_reason: "El agente no confirmó que el proceso se detuviera (sin respuesta). Requiere intervención manual.",
    attack: [[0, "INFO", "Wazuh", "Actividad de archivos fuera de lo normal en srv-files-01 (simulación controlada)"], [1, "WARN", "Wazuh", "Modificación masiva de archivos: patrón compatible con cifrado (130 archivos en 20s)"]],
    detect: [[2, "WARN", "Wazuh", "Comportamiento compatible con ransomware detectado (simulación controlada)"]],
    applied: ["Acción de contención aplicada sobre el proceso sospechoso.", "Host srv-files-01 aislado de la red de producción."],
    verifyLines: ["Verificando actividad de archivos en srv-files-01...", "Sin nuevas modificaciones masivas de archivos."],
    contained_msg: "El comportamiento compatible con ransomware fue contenido (simulación controlada).",
    failed_line: "No se pudo detener el proceso sospechoso (sin respuesta del agente).",
    outcomes: [
      { label: "Comportamiento contenido", detail: "Sin nuevas modificaciones masivas de archivos." },
      { label: "Proceso detenido", detail: "El proceso sospechoso fue detenido." },
      { label: "Host aislado", detail: "srv-files-01 contenido; no se propaga a otros equipos." },
      { label: "Empresa protegida", detail: "Los demás sistemas continúan operativos." },
    ],
    tools: [
      { name: "Wazuh", detail: "Monitoreo de integridad de archivos (FIM)", role: "HIDS" }, { name: "CyberShield Engine", detail: "Coordinación y respuesta automática", role: "Motor" },
      { name: "Wazuh Active Response", detail: "Ejecución de la acción defensiva", role: "Respuesta" }, { name: "PostgreSQL", detail: "Almacenamiento de eventos", role: "Base de datos" },
    ],
  },
};

/* Construye el payload (lo que entregaría el backend) del ataque y estado pedidos para el incidente `id`. */
export function buildMockEvidencePayload(id: string, attack: EvidenceAttack, scenario: EvidenceScenario): unknown {
  const A = ATTACKS[attack];
  const at = (s: number) => `${A.day}${String(s).padStart(2, "0")}Z`;
  const prompt = `root@${A.server}:~# `;
  const entry = (stage: EvidenceStage, s: number, level: LogLevel, source: string, message: string, extra: Partial<EvidenceEntry> = {}): EvidenceEntry => ({
    incident_id: id, event_id: 1, stage, timestamp: at(s), source, level, message, action_type: null, command_display: null, result: null, success: null, ...extra,
  });
  const cmd = (s: number, text: string): TerminalLine => ({ kind: "command", timestamp: at(s), text: prompt + text });
  const out = (s: number, level: LogLevel, text: string): TerminalLine => ({ kind: "output", timestamp: at(s), level, text });
  const blank: TerminalLine = { kind: "blank", text: "" };

  /* Etapas comunes: ataque -> detección -> regla -> incidente creado (los 4 primeros círculos). */
  const detectedEntries: EvidenceEntry[] = [
    ...A.attack.map(([s, l, src, m]) => entry("ATTACK_RECEIVED", s, l, src, m)),
    ...A.detect.map(([s, l, src, m]) => entry("DETECTED", s, l, src, m)),
    entry("DETECTED", 2, "INFO", "CyberShield", "Evento normalizado por CyberShield"),
    entry("DETECTED", 2, "INFO", "CyberShield", `Clasificación: ${A.mitre_id} - ${A.mitre_name} (${A.mitre_tactic})`),
    entry("RULE_APPLIED", 3, "INFO", "CyberShield", `Regla aplicada: ${A.rule}`),
    entry("INCIDENT_CREATED", 4, "INFO", "CyberShield", `Incidente creado: ${id} (Severidad: ${A.severity})`),
  ];
  const startEntry = entry("RESPONDING", 5, "INFO", "CyberShield", `Ejecutando acción de respuesta: ${A.actionVerb}`, { action_type: A.action_type, command_display: A.command_preview });

  const common = {
    incident_id: id, event_id: 1, event_type: A.event_type, severity: A.severity, server: A.server, source_ip: A.source_ip, rule: A.rule,
    mitre_id: A.mitre_id, mitre_name: A.mitre_name, mitre_tactic: A.mitre_tactic, scenario_note: A.scenario_note, detected_at: at(2), outcomes: [] as Outcome[], tools: A.tools, elapsed_time: null as number | null,
  };
  const resp = {
    action_type: A.action_type, tool: A.tool, command_display: null as string | null, command_preview: A.command_preview, reason: A.reason,
    result: null as string | null, success: null as boolean | null, failure_reason: null as string | null, notification: null as Notif | null,
  };

  if (scenario === "detected") return { ...common, status: "DETECTED", response_started_at: null, response_finished_at: null, verification_result: null,
    entries: detectedEntries, response: { ...resp, terminal_lines: [] } };

  if (scenario === "responding") return { ...common, status: "RESPONDING", response_started_at: at(5), response_finished_at: null, verification_result: null,
    entries: [...detectedEntries, startEntry, entry("RESPONDING", 6, "INFO", "Active Response", "Aplicando la acción defensiva...", { action_type: A.action_type })],
    response: { ...resp, terminal_lines: [cmd(5, A.command_preview), out(6, "INFO", "Aplicando la acción defensiva...")] } };

  if (scenario === "failed" || scenario === "escalated") {
    const esc = scenario === "escalated";
    const failEntry = entry("FAILED", 9, "ERROR", "Active Response", "La acción defensiva no se pudo ejecutar", { action_type: A.action_type, result: "failed", success: false });
    return { ...common, status: esc ? "ESCALATED" : "FAILED", response_started_at: at(5), response_finished_at: at(esc ? 10 : 9), verification_result: "failed",
      entries: [...detectedEntries, startEntry, failEntry,
        ...(esc ? [entry("ESCALATED", 10, "WARN", "CyberShield", "Incidente escalado al ingeniero de guardia (respuesta manual)", { action_type: A.action_type, result: "escalated" })] : [])],
      response: { ...resp, result: esc ? "escalated" : "failed", success: false, failure_reason: A.failure_reason,
        notification: { channel: "Telegram", status: esc ? "Enviada al ingeniero de guardia" : "Enviada (alerta de fallo)", notified: true }, // BACKEND_GISS: response.notification <- backend.notification {channel,status,notified}
        terminal_lines: [cmd(5, A.command_preview), out(9, "ERROR", A.failed_line), ...(esc ? [blank, out(10, "WARN", "Escalado: se requiere intervención del equipo de seguridad.")] : [])] } };
  }

  /* contained */
  return { ...common, status: "CONTAINED", response_started_at: at(5), response_finished_at: at(8), verification_result: "contained", // BACKEND_GISS: verification_result <- backend.response_action.verification_result
    entries: [...detectedEntries, startEntry,
      entry("RESPONDING", 6, "OK", "Active Response", "Acción defensiva aplicada correctamente", { action_type: A.action_type, result: "applied", success: true }),
      entry("RESPONDING", 7, "INFO", "CyberShield", A.verifyLines[0]),
      entry("CONTAINED", 8, "WARN", "CyberShield", A.verifyLines[1], { action_type: A.action_type, result: "denied", success: true }),
      entry("CONTAINED", 8, "OK", "CyberShield", A.contained_msg)],
    response: { ...resp, result: "contained", success: true,
      notification: { channel: "Telegram", status: "Enviada", notified: true }, // BACKEND_GISS: response.notification <- backend.notification {channel,status,notified}
      terminal_lines: [cmd(5, A.command_preview), ...A.applied.map((t) => out(6, "OK", t)), blank, out(7, "INFO", A.verifyLines[0]), out(8, "DENIED", A.verifyLines[1]), out(8, "INFO", A.contained_msg)] }, // BACKEND_GISS: response.terminal_lines <- backend.evidence.terminal_lines[] {kind, timestamp, level, text}
    outcomes: A.outcomes }; // BACKEND_GISS: outcomes[] <- backend.evidence.outcomes[] (solo si status=CONTAINED y verification_result=contained)
}
