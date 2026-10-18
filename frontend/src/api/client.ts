import axios from "axios";
import type {
  EventStats,
  Evento,
  IncidentStatus,
  Incidente,
  NotificationItem,
  Scope,
  ServerItem,
  ServerStatus,
  Stats,
  User,
} from "../types";
import { hhmm, stamp, toSeverity } from "../utils/format";

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
})

http.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("cs_token");
  if (token && token !== "mvp-session") cfg.headers.Authorization = `Bearer ${token}`;
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
  eventStats: "/events/stats",
  notifications: "/notifications",
};

export const isNet = (e: unknown) => axios.isAxiosError(e) && !e.response;

const incidentCode = (id: number) => `INC-${String(id).padStart(3, "0")}`;

const eventTitle = (eventType: string) => {
  const titles: Record<string, string> = {
    authentication_failure: "Intento de autenticación fallido",
    authentication_burst: "Patrón sospechoso de autenticación",
    multiple_login_attempts: "Múltiples intentos de autenticación",
    suspicious_file_change: "Cambio sospechoso de archivo",
    suspicious_network_traffic: "Tráfico de red sospechoso",
    unusual_external_connection: "Conexión externa inusual",
    unusual_outbound_connection_burst: "Conexiones salientes inusuales",
    privilege_escalation: "Escalación de privilegios",
  };
  return titles[eventType] ?? eventType.replaceAll("_", " ");
};

const eventSummary = (eventType: string) => {
  const summaries: Record<string, string> = {
    authentication_failure: "Se registró un intento de autenticación fallido.",
    authentication_burst: "Se detectó un patrón anormal de autenticación que requiere revisión.",
    multiple_login_attempts: "Se detectaron varios intentos de autenticación en una ventana corta.",
    suspicious_file_change: "CyberShield detectó una modificación de archivo que requiere validación.",
    suspicious_network_traffic: "Se detectó un patrón de tráfico fuera del comportamiento esperado.",
    unusual_external_connection: "Se detectó una conexión externa fuera del patrón esperado.",
    privilege_escalation: "Se observó actividad relacionada con privilegios elevados.",
  };
  return summaries[eventType] ?? "Evento de seguridad clasificado por CyberShield para revisión.";
};

const serviceLabel = (eventType: string) => {
  if (eventType.includes("authentication")) return "Autenticación";
  if (eventType.includes("file")) return "Sistema de archivos";
  if (eventType.includes("network") || eventType.includes("connection")) return "Red";
  if (eventType.includes("privilege")) return "Identidad / privilegios";
  return "Por determinar";
};

const ruleLabel = (eventType: string) => {
  if (eventType.includes("authentication")) return "AUTH-CORRELATION";
  if (eventType.includes("file")) return "FILE-CHANGE";
  if (eventType.includes("network") || eventType.includes("connection")) return "NETWORK-CORRELATION";
  if (eventType.includes("privilege")) return "PRIVILEGE-CORRELATION";
  return "CYBERSHIELD-RULE";
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

const normalizeScope = (value: unknown): Scope | null => {
  const scope = String(value ?? "").toUpperCase();
  if (scope === "BLOCKED" || scope === "REACHED" || scope === "IMPACT") return scope;
  return null;
};

export async function register(body: { name: string; email: string; password: string }) {
  const res = await http.post(ROUTES.register, body);
  return res.data.user as User;
}

export async function login(
  body: {
    email: string;
    password: string;
  }
) {
  try {
    const res = await http.post(
      ROUTES.login,
      body
    );

    return {
      token: "mvp-session",
      user: res.data.user as User,
    };

  } catch (error: any) {
    const status =
      error?.response?.status;

    const detail =
      error?.response?.data?.detail;

    if (status === 403) {
      throw new Error(
        detail ||
          "Acceso bloqueado: origen no autorizado."
      );
    }

    if (status === 401) {
      throw new Error(
        "Correo o contraseña incorrectos."
      );
    }

    if (!error?.response) {
      throw new Error(
        "No se pudo conectar con el servidor CyberShield."
      );
    }

    throw new Error(
      detail ||
        "No fue posible iniciar sesión."
    );
  }
}

export async function getDashboard(): Promise<Stats> {
  const res = await http.get(ROUTES.dashboard);
  const d = res.data ?? {};
  return {
    estado: "Monitoreo activo. Revisa los incidentes y eventos recientes.",
    servidores: Number(d.servers ?? 0),
    servidoresOnline: Number(d.servers_online ?? 0),
    servidoresOffline: Number(d.servers_offline ?? 0),
    eventos: Number(d.events ?? 0),
    incidentes: Number(d.incidents ?? 0),
    criticos: Number(d.critical_incidents ?? 0),
  };
}

export async function getEvents(): Promise<Evento[]> {
  const res = await http.get(ROUTES.events);
  const list = res.data ?? [];
  return list.map((e: any) => {
    const createdAt = e.created_at ?? e.createdAt ?? null;
    return {
      id: e.id,
      createdAt: createdAt ?? undefined,
      fecha: createdAt ? hhmm(new Date(createdAt)) : "—",
      tipo: String(e.event_type ?? e.tipo ?? "Evento"),
      origen: String(e.source_ip ?? e.origen ?? "—"),
      severidad: toSeverity(e.severity ?? e.severidad),
      estado: e.estado ?? (toSeverity(e.severity) === "NORMAL" ? "Registrado" : "Detectado"),
      scope: normalizeScope(e.scope),
      serverId: e.server_id != null ? Number(e.server_id) : null,
      serverName: e.server_name ?? e.hostname ?? null,
    };
  });
}

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
      servidor: i.server_name ?? i.hostname ?? (i.server_id != null ? `Servidor #${i.server_id}` : "srv-cyber-01"),
      servicio: serviceLabel(eventType),
      detectado: i.created_at ? stamp(i.created_at) : stamp(),
      asignado: "—",
      regla: ruleLabel(eventType),
      reco: i.recommendation ?? "Revisar el evento asociado, su contexto y la evidencia antes de aplicar una respuesta.",
      investigationSteps: Array.isArray(i.investigation_steps) && i.investigation_steps.length
        ? i.investigation_steps
        : ["Revisar el evento asociado.", "Validar el origen y el servidor.", "Buscar actividad relacionada."],
      resolutionCriteria: i.resolution_criteria ?? "El evento fue investigado y existe evidencia suficiente para considerarlo legítimo, contenido o resuelto.",
    };
  });
}

export async function updateIncidentStatus(id: number, status: "investigating" | "resolved") {
  const res = await http.patch(`${ROUTES.incidents}/${id}/status`, { status });
  return res.data;
}

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

export async function getEventStats(window: "1s" | "60s"): Promise<EventStats> {
  const res = await http.get(ROUTES.eventStats, { params: { window } });
  const r = res.data ?? {};
  return {
    window,
    window_seconds: Number(r.window_seconds ?? (window === "1s" ? 1 : 60)),
    total_events: Number(r.total_events ?? 0),
    by_source: (r.by_source ?? []).map((x: any) => ({ source_ip: x.source_ip ?? null, count: Number(x.count ?? 0) })),
    by_type: (r.by_type ?? []).map((x: any) => ({ event_type: String(x.event_type ?? ""), count: Number(x.count ?? 0) })),
    by_scope: {
      BLOCKED: Number(r.by_scope?.BLOCKED ?? 0),
      REACHED: Number(r.by_scope?.REACHED ?? 0),
      IMPACT: Number(r.by_scope?.IMPACT ?? 0),
    },
    by_server: (r.by_server ?? []).map((x: any) => ({ server_id: x.server_id ?? null, count: Number(x.count ?? 0) })),
  };
}

export async function getNotifications(): Promise<NotificationItem[]> {
  const res = await http.get(ROUTES.notifications);
  return (res.data ?? []).map((n: any) => ({
    id: Number(n.id),
    incident_id: Number(n.incident_id),
    severity: toSeverity(n.severity),
    recipient: String(n.recipient ?? ""),
    channel: String(n.channel ?? ""),
    message: String(n.message ?? ""),
    status: String(n.status ?? ""),
    created_at: String(n.created_at ?? ""),
    sent_at: n.sent_at ?? null,
  }));
}

export async function simulateEvent(userName?: string): Promise<Incidente | null> {
  const body = {
    event_type: "authentication_burst",
    source: "simulator",
    source_ip: "192.168.1.50",
    server_id: 2,
    user: userName ?? "usuario_demo",
    description: "Patrón sospechoso contra múltiples cuentas",
    details: {
      attempts: 15,
      time_window_seconds: 60,
      distinct_users: 5,
      successful_login: false,
      unauthorized_access: false,
      privilege_escalation: false,
    },
  };

  const res = await http.post(ROUTES.simulate, body);
  const inc = res.data?.incident;
  if (!inc?.id) return null;
  const incidents = await getIncidents();
  const full = incidents.find((item) => item.backendId === Number(inc.id));
  return full ? { ...full, asignado: userName ?? full.asignado } : null;
}
