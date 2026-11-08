import axios from "axios";
import type {
  IncidentEvidence,
} from "../types/evidence";
import type {
  EventStats,
  Evento,
  IncidentStatus,
  Incidente,
  MitreTechnique,
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

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      axios.isAxiosError(error) &&
      error.response?.status === 401
    ) {
      const url = error.config?.url ?? "";

      const sentAuthorization =
        error.config?.headers?.get?.("Authorization") ??
        error.config?.headers?.Authorization;

      const currentToken =
        localStorage.getItem("cs_token");

      if (
        !url.startsWith("/auth/") &&
        typeof sentAuthorization === "string" &&
        currentToken &&
        sentAuthorization === `Bearer ${currentToken}`
      ) {
        window.dispatchEvent(
          new Event("cybershield:session-expired")
        );
      }
    }

    return Promise.reject(error);
  }
);

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

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

export async function api<T = any>(path: string, method: "GET" | "POST" = "GET", body?: unknown, signal?: AbortSignal): Promise<T> {
  try {
    const res = await http.request<T>({ url: path, method, data: body, signal });
    return res.data;
  } catch (e) {
    if (axios.isAxiosError(e) && e.response) {
      const d = (e.response.data as any)?.detail;
      const msg = typeof d === "string" ? d : Array.isArray(d) ? d.map((x: any) => x.msg).join(", ") : "Error del servidor";
      throw new ApiError(msg, e.response.status);
    }
    throw e;
  }
}

export const isMissing = (e: unknown) => e instanceof ApiError && [404, 405, 501].includes(e.status);

export function normalizeMitre(v: any): MitreTechnique[] {
  const raw = Array.isArray(v) ? v : v ? [v] : [];

  return raw
    .map((x: any) => ({
      technique_id: String(
        x?.technique_id ?? x?.id ?? ""
      ),
      technique_name: String(
        x?.technique_name ?? x?.name ?? ""
      ),
      tactic: x?.tactic ?? null,
      url:
        x?.reference_url ??
        x?.url ??
        null,
      is_primary: Boolean(
        x?.is_primary ?? true
      ),
      rationale:
        x?.notes ??
        x?.rationale ??
        x?.justification ??
        null,
    }))
    .filter((t) => t.technique_id);
}

export const incidentCode = (id: number) => `INC-${String(id).padStart(3, "0")}`;

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
  if (value === "escalated") return "Escalado";

  return "Pendiente";
};

const normalizeStatus = (
  status: unknown
): IncidentStatus => {
  const value = String(
    status ?? "open"
  ).toLowerCase();

  if (value === "resolved") {
    return "resolved";
  }

  if (value === "investigating") {
    return "investigating";
  }

  if (value === "escalated") {
    return "escalated";
  }

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
      token: res.data.access_token as string,
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

  const rawList: any[] =
    Array.isArray(res.data)
      ? res.data
      : [];

  console.log(
  "[INCIDENTS] backend:",
  rawList.length
);

  // ==========================================================
  // DEDUPLICACIÓN VISUAL DE INCIDENTES HISTÓRICOS
  //
  // No elimina registros de PostgreSQL.
  // Solo agrupa incidentes que representan la misma ráfaga:
  //
  // - misma familia/tipo de ataque
  // - misma IP origen
  // - mismo servidor
  // - mismo usuario, cuando el backend lo proporciona
  // - separados por menos de 5 minutos
  //
  // Los eventos originales siguen existiendo.
  // ==========================================================

  const AUTH_TYPES = new Set([
    "authentication_failure",
    "multiple_login_attempts",
    "authentication_burst",
  ]);

  const familyOf = (item: any) => {
    const type = String(
      item.event_type ??
      "security_incident"
    );

    if (AUTH_TYPES.has(type)) {
      return "authentication_attack";
    }

    return type;
  };

  const userOf = (item: any) =>
    String(
      item.user ??
      item.details?.user ??
      item.event_details?.user ??
      ""
    );

  const keyOf = (item: any) => [
    familyOf(item),

    String(
      item.source_ip ??
      "NO_SOURCE_IP"
    ),

    String(
      item.server_id ??
      "NO_SERVER"
    ),

    userOf(item),
  ].join("|");

  const timestampOf = (
    item: any
  ): number | null => {
    if (!item.created_at) {
      return null;
    }

    const value = Date.parse(
      item.created_at
    );

    return Number.isFinite(value)
      ? value
      : null;
  };

  // Preferir el incidente que tenga
  // la mejor evidencia defensiva.
  const qualityOf = (item: any) => {
    const actionStatus = String(
      item.response_action?.status ?? ""
    ).toLowerCase();

    const incidentStatus = String(
      item.status ?? ""
    ).toLowerCase();

    const actionRank: Record<
      string,
      number
    > = {
      rolled_back: 50,
      executed: 40,
      failed: 30,
      pending: 20,
      approved: 10,
    };

    const incidentRank: Record<
      string,
      number
    > = {
      resolved: 8,
      investigating: 6,
      escalated: 5,
      open: 4,
    };

    return (
      (actionRank[actionStatus] ?? 0) +
      (incidentRank[incidentStatus] ?? 0)
    );
  };

  const FIVE_MINUTES =
    5 * 60 * 1000;

  const ordered = [...rawList].sort(
    (a, b) => {
      const ta =
        timestampOf(a) ?? 0;

      const tb =
        timestampOf(b) ?? 0;

      return ta - tb;
    }
  );

  const clusters = new Map<
    string,
    {
      lastTimestamp: number;
      best: any;
    }
  >();

  const list: any[] = [];

  for (const item of ordered) {
    const timestamp =
      timestampOf(item);

    // Si no tenemos hora fiable,
    // no lo agrupamos a ciegas.
    if (timestamp == null) {
      list.push(item);
      continue;
    }

    const key = keyOf(item);

    const current =
      clusters.get(key);

    // Primer incidente de esta familia.
    if (!current) {
      clusters.set(key, {
        lastTimestamp: timestamp,
        best: item,
      });

      continue;
    }

    const sameBurst =
      timestamp -
        current.lastTimestamp
      <= FIVE_MINUTES;

    // Si ya pasó la ventana,
    // el anterior sí representa
    // un incidente independiente.
    if (!sameBurst) {
      list.push(current.best);

      clusters.set(key, {
        lastTimestamp: timestamp,
        best: item,
      });

      continue;
    }

    // Sigue siendo la misma ráfaga.
    current.lastTimestamp =
      timestamp;

    const currentQuality =
      qualityOf(current.best);

    const candidateQuality =
      qualityOf(item);

    const currentCorrelated =
      Math.max(
        1,
        Number(
          current.best.correlated_events_count ?? 1
        ),
      );

    const candidateCorrelated =
      Math.max(
        1,
        Number(
          item.correlated_events_count ?? 1
        ),
      );

    // Primero preferimos el incidente que tenga
    // más eventos realmente correlacionados por backend.
    //
    // Si ambos tienen el mismo conteo, conservamos
    // el que tenga mejor respuesta/evidencia.
    //
    // En empate total, conservamos el más reciente.
    if (
      candidateCorrelated >
        currentCorrelated ||
      (
        candidateCorrelated ===
          currentCorrelated &&
        (
          candidateQuality >
            currentQuality ||
          (
            candidateQuality ===
              currentQuality &&
            Number(item.id) >
              Number(current.best.id)
          )
        )
      )
    ) {
      current.best = item;
    }
  }

  for (const cluster of clusters.values()) {
    list.push(cluster.best);
  }

  // Mostrar los incidentes más recientes primero.
  list.sort((a, b) => {
    const ta =
      timestampOf(a) ??
      Number(a.id) ??
      0;

    const tb =
      timestampOf(b) ??
      Number(b.id) ??
      0;

    return tb - ta;
  });

  console.log(
  "[INCIDENTS] después de deduplicar:",
  list.length
);

  return list.map((i: any) => {
    const backendId = Number(i.id);
    const eventType = String(i.event_type ?? "security_incident");
    const status = normalizeStatus(i.status);
    return {
      id: incidentCode(backendId),
      backendId,
      eventId: i.event_id != null ? Number(i.event_id) : undefined,
      eventType,
      correlatedEventsCount: Math.max(
        1,
        Number(
          i.correlated_events_count ?? 1
        ),
      ),
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
      mitre: normalizeMitre(i.mitre_techniques ?? i.mitre ?? i.techniques),
      responseAction: i.response_action
  ? {
      id: Number(i.response_action.id),
      action_type: String(
        i.response_action.action_type ?? ""
      ),
      target:
        i.response_action.target ?? null,
      status:
        i.response_action.status ?? "pending",
      reversible:
        Boolean(i.response_action.reversible),
      duration_seconds:
        i.response_action.duration_seconds != null
          ? Number(
              i.response_action.duration_seconds
            )
          : null,
      reason:
        i.response_action.reason ?? null,
      result:
        i.response_action.result ?? null,
      created_at:
        i.response_action.created_at ?? null,
      executed_at:
        i.response_action.executed_at ?? null,
      rolled_back_at:
        i.response_action.rolled_back_at ?? null,
    }
  : null,
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

export async function getNotifications(
  visibleIncidents?: Incidente[]
): Promise<NotificationItem[]> {
  const res = await http.get(ROUTES.notifications);

  const rawList: any[] = Array.isArray(res.data)
    ? res.data
    : [];

  /*
   * DEDUPLICACIÓN VISUAL
   *
   * La BD conserva todas las notificaciones.
   * La interfaz muestra una sola notificación
   * por incidente actualmente visible.
   */

  // El dashboard ya cargó los incidentes durante
  // este mismo ciclo. Los reutilizamos para evitar
  // una segunda petición GET /incidents.
  //
  // El fallback mantiene compatibilidad con otros
  // consumidores que llamen getNotifications()
  // directamente.
  const incidentsForVisibility =
    visibleIncidents ?? await getIncidents();

  const visibleIncidentIds = new Set(
    incidentsForVisibility
      .map((incident) => Number(incident.backendId))
      .filter((id) => Number.isFinite(id)),
  );

  const timestampOf = (notification: any) => {
    const raw =
      notification.sent_at ??
      notification.created_at ??
      "";

    const timestamp = Date.parse(raw);

    return Number.isFinite(timestamp)
      ? timestamp
      : Number(notification.id) || 0;
  };

  const latestByIncident = new Map<number, any>();

  for (const notification of rawList) {
    const incidentId = Number(notification.incident_id);

    if (!Number.isFinite(incidentId)) {
      continue;
    }

    // Ignorar notificaciones de incidentes históricos
    // que ya fueron agrupados visualmente.
    if (!visibleIncidentIds.has(incidentId)) {
      continue;
    }

    const current = latestByIncident.get(incidentId);

    if (
      !current ||
      timestampOf(notification) > timestampOf(current) ||
      (
        timestampOf(notification) === timestampOf(current) &&
        Number(notification.id) > Number(current.id)
      )
    ) {
      latestByIncident.set(incidentId, notification);
    }
  }

  const list = Array.from(
    latestByIncident.values(),
  ).sort(
    (a, b) => timestampOf(b) - timestampOf(a),
  );

  console.log(
    "[NOTIFICATIONS] backend:",
    rawList.length,
  );

  console.log(
    "[NOTIFICATIONS] después de agrupar:",
    list.length,
  );

  return list.map((n: any) => ({
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
export async function getIncidentEvidence(
  id: number | string
): Promise<IncidentEvidence> {
  const raw = String(id);

  const normalized = raw
    .toUpperCase()
    .startsWith("INC-")
    ? raw.slice(4)
    : raw;

  const incidentId = Number(normalized);

  if (!Number.isFinite(incidentId)) {
    throw new Error(
      "ID de incidente inválido"
    );
  }

  return api<IncidentEvidence>(
    `/incidents/${incidentId}/evidence`
  );
}
