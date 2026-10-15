export type Severidad = "NORMAL" | "WARNING" | "HIGH" | "CRITICAL";
export type Scope = "BLOCKED" | "REACHED" | "IMPACT";
export type IncidentStatus = "open" | "investigating" | "resolved";
export type ServerStatus = "online" | "offline" | "registered";

export interface Evento {
  id: number | string;
  fecha: string;
  createdAt?: string;
  tipo: string;
  origen: string;
  severidad: Severidad;
  estado: string;
  scope: Scope | null;
  serverId: number | null;
  serverName?: string | null;
}

export interface Incidente {
  id: string;
  backendId: number;
  eventId?: number;
  eventType?: string;
  titulo: string;
  resumen: string;
  severidad: Severidad;
  estado: "Pendiente" | "Investigando" | "Resuelto" | string;
  status: IncidentStatus;
  origen: string;
  servidor: string;
  servicio: string;
  detectado: string;
  asignado: string;
  regla: string;
  reco: string;
  investigationSteps: string[];
  resolutionCriteria: string;
}

export interface ServerItem {
  id: number;
  name: string;
  ipAddress: string;
  status: ServerStatus;
  agent: string | null;
  createdAt?: string | null;
  lastSeen: string | null;
}

export interface Stats {
  estado: string;
  servidores: number;
  servidoresOnline: number;
  servidoresOffline: number;
  eventos: number;
  incidentes: number;
  criticos: number;
}

export interface EventStats {
  window: "1s" | "60s";
  window_seconds: number;
  total_events: number;
  by_source: { source_ip: string | null; count: number }[];
  by_type: { event_type: string; count: number }[];
  by_scope: Record<Scope, number>;
  by_server: { server_id: number | null; count: number }[];
}

export interface NotificationItem {
  id: number;
  incident_id: number;
  severity: Severidad;
  recipient: string;
  channel: string;
  message: string;
  status: string;
  created_at: string;
  sent_at: string | null;
}

export interface User {
  id?: number;
  name: string;
  email?: string;
}
