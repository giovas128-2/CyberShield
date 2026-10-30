/* ============================================================================================================
   CAPA DE DATOS DEL FRONTEND DESACOPLADO (D4)
   Esta capa NO hace ninguna petición de red: no usa fetch, axios, WebSocket ni URLs. Cada función devuelve datos de
   src/mocks/mockData.ts (el ÚNICO mock) con una pequeña espera simulada para que se vean los estados de carga.

   Los nombres, parámetros y tipos de retorno de las funciones exportadas son EXACTAMENTE los que usa el resto de la app.
   Giss: para conectar el backend, reemplaza SOLO el cuerpo de cada función marcada BACKEND_GISS (la firma no cambia)
   y deja intactos los componentes. Pasos exactos en README_INTEGRACION_GISS.md; contrato de campos en MAPEO_BACKEND_FRONTEND.md.
   ============================================================================================================ */
import type { EventStats, Evento, Incidente, IncidentStatus, MitreTechnique, NotificationItem, ServerItem, Stats, User } from "../types";
import { stamp } from "../utils/format";
import {
  MOCK_DASHBOARD, MOCK_EVENTS, MOCK_EVENT_STATS, MOCK_INCIDENTS, MOCK_NOTIFICATIONS, MOCK_SERVERS, MOCK_USER,
} from "../mocks/mockData";

const wait = (ms = 120) => new Promise<void>((r) => setTimeout(r, ms));
const clone = <T,>(v: T): T => JSON.parse(JSON.stringify(v)) as T;

/* Estado en memoria (solo mock): permite que "Simular evento" y "Cambiar estado del incidente" se vean reflejados al recargar la lista.
   BACKEND_GISS: este objeto desaparece; el estado vive en el backend. */
const mem = { events: clone(MOCK_EVENTS) as Evento[], incidents: clone(MOCK_INCIDENTS) as Incidente[], users: [] as { name: string; email: string }[] };

/* ---------- Utilidades que NO son red (se conservan tal cual para Giss) ---------- */
export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}
/* BACKEND_GISS: con backend real, isNet = error sin respuesta del servidor y isMissing = 404/405/501 (ver cliente del proyecto maestro). */
export const isNet = (_e: unknown) => false;
export const isMissing = (e: unknown) => e instanceof ApiError && [404, 405, 501].includes(e.status);

export const incidentCode = (id: number) => `INC-${String(id).padStart(3, "0")}`;

export function normalizeMitre(v: any): MitreTechnique[] {
  const raw = Array.isArray(v) ? v : v ? [v] : [];
  return raw
    .map((x: any) => ({
      technique_id: String(x?.technique_id ?? x?.id ?? ""),
      technique_name: String(x?.technique_name ?? x?.name ?? ""),
      tactic: x?.tactic ?? null,
      url: x?.reference_url ?? x?.url ?? null,
      is_primary: Boolean(x?.is_primary ?? true),
      rationale: x?.notes ?? x?.rationale ?? x?.justification ?? null,
    }))
    .filter((t: MitreTechnique) => t.technique_id);
}

/* ---------- Sesión ---------- */
/* BACKEND_GISS: register <- enviar {name,email,password} al registro del backend; devolver user {id,name,email}. Error "correo ya registrado" -> Error con ese texto. */
export async function register(body: { name: string; email: string; password: string }): Promise<User> {
  await wait();
  if (mem.users.some((u) => u.email.toLowerCase() === body.email.toLowerCase())) throw new Error("Ese correo ya está registrado.");
  mem.users.push({ name: body.name, email: body.email }); // la contraseña NO se guarda en el mock
  return { ...MOCK_USER, name: body.name, email: body.email };
}

/* BACKEND_GISS: login <- enviar {email,password} al login del backend; devolver {token, user}. Mensajes de error que la pantalla ya muestra:
   401 "Correo o contraseña incorrectos." · 403 detail del backend (origen no autorizado) · sin red "No se pudo conectar con el servidor CyberShield."
   MOCK: acepta cualquier correo/contraseña con formato válido (la validación de formato la hace Login.tsx). */
export async function login(body: { email: string; password: string }): Promise<{ token: string; user: User }> {
  await wait();
  const known = mem.users.find((u) => u.email.toLowerCase() === body.email.toLowerCase());
  const name = known?.name ?? MOCK_USER.name;
  return { token: "mvp-session", user: { ...MOCK_USER, name, email: body.email } };
}

/* ---------- Dashboard ---------- */
/* BACKEND_GISS: getDashboard <- resumen del dashboard {servers, servers_online, servers_offline, events, incidents, critical_incidents}. */
export async function getDashboard(): Promise<Stats> {
  await wait();
  return clone(MOCK_DASHBOARD);
}

/* ---------- Eventos ---------- */
/* BACKEND_GISS: getEvents <- lista de eventos del backend (campos en mocks/mockData.ts §3 y MAPEO_BACKEND_FRONTEND.md). Orden: la pantalla reordena por createdAt. */
export async function getEvents(): Promise<Evento[]> {
  await wait();
  return clone(mem.events);
}

/* ---------- Incidentes ---------- */
/* BACKEND_GISS: getIncidents <- lista de incidentes del backend (campos en mocks/mockData.ts §4). El código INC-xxx se arma con incidentCode(incident.id). */
export async function getIncidents(): Promise<Incidente[]> {
  await wait();
  return clone(mem.incidents);
}

/* BACKEND_GISS: updateIncidentStatus <- cambiar el estado del incidente `id` a "investigating" | "resolved" en el backend. */
export async function updateIncidentStatus(id: number, status: "investigating" | "resolved") {
  await wait();
  const inc = mem.incidents.find((i) => i.backendId === id);
  if (!inc) throw new ApiError("Incidente no encontrado", 404);
  inc.status = status as IncidentStatus;
  inc.estado = status === "resolved" ? "Resuelto" : "Investigando";
  return { id, status };
}

/* ---------- Servidores ---------- */
/* BACKEND_GISS: getServers <- lista de servidores del backend (campos en mocks/mockData.ts §2). */
export async function getServers(): Promise<ServerItem[]> {
  await wait();
  return clone(MOCK_SERVERS);
}

/* ---------- Estadísticas de eventos ---------- */
/* BACKEND_GISS: getEventStats <- estadísticas de eventos de la ventana `window` ("1s" | "60s") (campos en mocks/mockData.ts §6). */
export async function getEventStats(window: "1s" | "60s"): Promise<EventStats> {
  await wait();
  return clone(MOCK_EVENT_STATS[window]);
}

/* ---------- Notificaciones ---------- */
/* BACKEND_GISS: getNotifications <- lista de notificaciones enviadas (campos en mocks/mockData.ts §7). */
export async function getNotifications(): Promise<NotificationItem[]> {
  await wait();
  return clone(MOCK_NOTIFICATIONS);
}

/* ---------- Simulación (botón "Simular evento HIGH") ---------- */
/* BACKEND_GISS: simulateEvent <- pedir al backend que genere un evento de prueba y devolver el incidente creado (ya normalizado como Incidente).
   MOCK: agrega a la memoria un evento HIGH y un incidente nuevo. */
export async function simulateEvent(userName?: string): Promise<Incidente | null> {
  await wait(250);
  const n = mem.incidents.reduce((m, i) => Math.max(m, i.backendId), 0) + 1;
  const now = new Date();
  mem.events.push({ id: 1000 + n, fecha: now.toTimeString().slice(0, 5), createdAt: now.toISOString(), tipo: "authentication_burst", origen: "192.168.1.50", severidad: "HIGH", estado: "Detectado", scope: "REACHED", serverId: 2, serverName: "srv-cyber-01" });
  const inc: Incidente = {
    id: incidentCode(n), backendId: n, eventType: "authentication_burst",
    titulo: "Patrón sospechoso de autenticación", resumen: "Se detectó un patrón anormal de autenticación que requiere revisión.",
    severidad: "HIGH", estado: "Pendiente", status: "open", origen: "192.168.1.50", servidor: "srv-cyber-01", servicio: "Autenticación",
    detectado: stamp(), asignado: userName ?? "—", regla: "AUTH-CORRELATION",
    reco: "Validar el origen, las cuentas afectadas y si hubo acceso exitoso posterior.",
    investigationSteps: ["Revisar origen y cuentas afectadas.", "Correlacionar fallos y accesos exitosos.", "Buscar actividad privilegiada posterior."],
    mitre: [], resolutionCriteria: "La actividad quedó explicada o contenida con evidencia suficiente.",
  };
  mem.incidents.unshift(inc);
  return clone(inc);
}

/* ---------- Laboratorio ---------- */
/* BACKEND_GISS: runLabScenario <- pedir al backend que ejecute el escenario `id` del laboratorio (simulación controlada, datos ficticios). */
export async function runLabScenario(_id: string): Promise<void> {
  await wait(1200);
}
