import axios from "axios";
import type {
  Evento,
  IncidentStatus,
  Incidente,
  ServerItem,
  ServerStatus,
  Stats,
  User,
} from "../types";
import { hhmm, stamp, toSeverity } from "../utils/format";

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

http.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("cs_token");

  // El MVP usa una sesión local mientras el backend todavía no emite JWT.
  // Cuando exista un JWT real, se enviará automáticamente.
  if (token && token !== "mvp-session") {
    cfg.headers.Authorization = `Bearer ${token}`;
  }

  return cfg;
});

export const ROUTES = {
  login: "/auth/login",
  register: "/auth/register",
  dashboard: "/dashboard/summary",
  events: "/events",
  incidents: "/incidents",
  servers: "/servers",
  simulate: "/events/simulate",
};

export const isNet = (e: unknown) => axios.isAxiosError(e) && !e.response;

const incidentCode = (id: number) => `INC-${String(id).padStart(3, "0")}`;

const eventTitle = (eventType: string) => {
  const titles: Record<string, string> = {
    multiple_login_attempts: "Múltiples intentos de autenticación",
    suspicious_file_change: "Cambio sospechoso de archivo",
    suspicious_network_traffic: "Tráfico de red sospechoso",
    unusual_outbound_connection_burst: "Conexiones salientes inusuales",
  };

  return titles[eventType] ?? eventType.replaceAll("_", " ") ?? "Incidente de seguridad";
};

const eventSummary = (eventType: string) => {
  const summaries: Record<string, string> = {
    multiple_login_attempts:
      "Se detectaron varios intentos de autenticación en una ventana corta de tiempo.",
    suspicious_file_change:
      "CyberShield detectó una modificación de archivo que requiere validación.",
    suspicious_network_traffic:
      "Se detectó un patrón de tráfico de red fuera del comportamiento esperado.",
    unusual_outbound_connection_burst:
      "Se detectaron conexiones salientes repetitivas hacia un destino externo poco habitual.",
  };

  return summaries[eventType] ?? "Evento de seguridad clasificado por CyberShield para revisión.";
};

const serviceLabel = (eventType: string) => {
  if (eventType === "multiple_login_attempts") return "Autenticación";
  if (eventType === "suspicious_file_change") return "Sistema de archivos";
  if (eventType === "suspicious_network_traffic") return "Red";
  if (eventType === "unusual_outbound_connection_burst") return "Red saliente";
  return "Por determinar";
};

const ruleLabel = (eventType: string) => {
  if (eventType === "multiple_login_attempts") return "AUTH-FAIL-MVP";
  if (eventType === "suspicious_file_change") return "FILE-CHANGE-MVP";
  if (eventType === "suspicious_network_traffic") return "NETWORK-MVP";
  if (eventType === "unusual_outbound_connection_burst") return "OUTBOUND-MVP";
  return "MVP-RULE";
};

const statusToUi = (status: string) => {
  const value = String(status ?? "open").toLowerCase();
  if (value === "resolved") return "Resuelto";
  if (value === "investigating") return "Investigando";
  return "Pendiente";
};

const normalizeStatus = (status: unknown): IncidentStatus => {
  const value = String(status ?? "open").toLowerCase();
  if (value === "resolved") return "resolved";
  if (value === "investigating") return "investigating";
  return "open";
};

const normalizeServerStatus = (status: unknown): ServerStatus => {
  const value = String(status ?? "registered").toLowerCase();
  if (value === "online") return "online";
  if (value === "offline") return "offline";
  return "registered";
};

/* =========================
   AUTH
========================= */

export async function register(body: {
  name: string;
  email: string;
  password: string;
}) {
  const res = await http.post(ROUTES.register, body);
  return res.data.user as User;
}

export async function login(body: {
  email: string;
  password: string;
}) {
  const res = await http.post(ROUTES.login, body);

  return {
    token: "mvp-session",
    user: res.data.user as User,
  };
}

/* =========================
   DASHBOARD
========================= */

export async function getDashboard(): Promise<Stats> {
  const res = await http.get(ROUTES.dashboard);
  const d = res.data;

  return {
    estado:
      d.status === "high_risk"
        ? "Riesgo alto: revisa los incidentes recientes."
        : d.status === "warning"
          ? "Advertencia: existen incidentes que requieren revisión."
          : "Sin amenazas críticas detectadas.",
    servidores: Number(d.servers ?? 0),
    eventos: Number(d.events ?? 0),
    incidentes: Number(d.incidents ?? 0),
    riesgo: Number(d.risk_score ?? 0),
  };
}

/* =========================
   EVENTS
========================= */

export async function getEvents(): Promise<Evento[]> {
  const res = await http.get(ROUTES.events);
  const list = res.data ?? [];

  return list.map((e: any) => {
    const createdAt = e.created_at ?? e.createdAt ?? null;
    const severity = String(e.severity ?? e.severidad ?? "").toLowerCase();

    return {
      id: e.id,
      createdAt: createdAt ?? undefined,
      fecha: createdAt ? hhmm(new Date(createdAt)) : "—",
      tipo: e.event_type ?? e.tipo ?? "Evento",
      origen: String(e.source_ip ?? e.origen ?? "—"),
      severidad: toSeverity(e.severity ?? e.severidad),
      estado:
        e.estado ??
        (severity === "high" || severity === "critical" ? "Detectado" : "Registrado"),
    };
  });
}

/* =========================
   INCIDENTS
========================= */

export async function getIncidents(): Promise<Incidente[]> {
  const res = await http.get(ROUTES.incidents);
  const list = res.data ?? [];

  return list.map((i: any) => {
    const backendId = Number(i.id);
    const eventType = String(i.event_type ?? "security_incident");
    const status = normalizeStatus(i.status);

    return {
      id: incidentCode(backendId),
      backendId,
      eventId: i.event_id != null ? Number(i.event_id) : undefined,
      eventType,
      titulo: eventTitle(eventType),
      resumen: eventSummary(eventType),
      severidad: toSeverity(i.severity),
      estado: statusToUi(status),
      status,
      origen: String(i.source_ip ?? "—"),
      servidor: i.server_name ?? i.hostname ?? "srv-cyber-01",
      servicio: serviceLabel(eventType),
      detectado: i.created_at ? stamp(i.created_at) : stamp(),
      asignado: "—",
      regla: ruleLabel(eventType),
      reco:
        i.recommendation ??
        "Revisar el evento asociado y validar si la actividad está autorizada.",
      investigationSteps:
        Array.isArray(i.investigation_steps) && i.investigation_steps.length
          ? i.investigation_steps
          : [
              "Revisar los datos del evento.",
              "Validar el origen.",
              "Buscar actividad relacionada.",
            ],
      resolutionCriteria:
        i.resolution_criteria ??
        "El evento fue investigado y existe evidencia suficiente para considerarlo legítimo o mitigado.",
    };
  });
}

export async function updateIncidentStatus(
  id: number,
  status: "investigating" | "resolved",
) {
  const res = await http.patch(`${ROUTES.incidents}/${id}/status`, { status });
  return res.data;
}

/* =========================
   SERVERS
========================= */

export async function getServers(): Promise<ServerItem[]> {
  const res = await http.get(ROUTES.servers);
  const list = res.data ?? [];

  return list.map((s: any) => ({
    id: Number(s.id),
    name: s.name ?? "—",
    ipAddress: String(s.ip_address ?? s.ip ?? "—"),
    status: normalizeServerStatus(s.status),
    agent: s.agent ?? null,
    createdAt: s.created_at ?? null,
    lastSeen: s.last_seen ?? null,
  }));
}

/* =========================
   SIMULATOR
========================= */

export async function simulateEvent(userName?: string): Promise<Incidente> {
  const body = {
    event_type: "multiple_login_attempts",
    source: "simulator",
    source_ip: "192.168.1.50",
    description: "Se detectaron múltiples intentos de autenticación",
    details: {
      attempts: 8,
      time_window_seconds: 30,
    },
  };

  const res = await http.post(ROUTES.simulate, body);
  const result = res.data;
  const event = result?.event ?? {};
  const inc = result?.incident;

  // Si el backend creó un incidente, volvemos a consultar /incidents para
  // obtener también la guía de investigación que proviene del trabajo de Danniel.
  if (inc?.id != null) {
    const incidents = await getIncidents();
    const full = incidents.find((item) => item.backendId === Number(inc.id));
    if (full) {
      return { ...full, asignado: userName ?? full.asignado };
    }
  }

  const fallbackId = Number(inc?.id ?? event?.id ?? Date.now());
  const eventType = String(event?.event_type ?? "multiple_login_attempts");
  const status: IncidentStatus = inc ? normalizeStatus(inc.status) : "open";

  return {
    id: inc ? incidentCode(fallbackId) : `EVT-${event.id ?? fallbackId}`,
    backendId: Number(inc?.id ?? 0),
    eventId: event?.id != null ? Number(event.id) : undefined,
    eventType,
    titulo: eventTitle(eventType),
    resumen: event?.description ?? eventSummary(eventType),
    severidad: toSeverity(inc?.severity ?? event?.severity),
    estado: inc ? statusToUi(status) : "Pendiente",
    status,
    origen: String(event?.source_ip ?? "192.168.1.50"),
    servidor: "srv-cyber-01",
    servicio: serviceLabel(eventType),
    detectado: event?.created_at ? stamp(event.created_at) : stamp(),
    asignado: userName ?? "—",
    regla: ruleLabel(eventType),
    reco: "Revisar actividad del servidor y registros de autenticación.",
    investigationSteps: [
      "Identificar la IP de origen.",
      "Revisar el usuario afectado.",
      "Comprobar la cantidad de intentos y la ventana de tiempo.",
    ],
    resolutionCriteria:
      "La actividad fue validada como legítima o se aplicó una mitigación autorizada.",
  };
}
