export type Severidad = "NORMAL" | "WARNING" | "HIGH" | "CRITICAL";
export type Scope = "BLOCKED" | "REACHED" | "IMPACT";
export type IncidentStatus = "open" | "investigating" | "resolved" | "escalated";
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
  mitre: MitreTechnique[];
  responseAction?: IncidentResponseAction | null;
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


export interface MitreTechnique {
  technique_id: string;
  technique_name: string;
  tactic: string | null;
  url: string | null;
  is_primary: boolean;
  rationale: string | null;
}
export interface IncidentResponseAction {
  id: number;
  action_type: string;
  target: string | null;
  status:
    | "pending"
    | "approved"
    | "executed"
    | "failed"
    | "rolled_back"
    | "cancelled";
  reversible: boolean;
  duration_seconds: number | null;
  reason: string | null;
  result: string | null;
  created_at: string | null;
  executed_at: string | null;
  rolled_back_at: string | null;
}

export type SourceMode = "integrated" | "simulated" | "pending";
export interface Device { id: string; name: string; user: string | null; os: string | null; status: "trusted" | "unauthorized" | "unknown"; last_seen: string | null; mode: SourceMode }
export interface SessionItem { id: string; user: string; device: string | null; ip: string | null; started_at: string | null; status: "active" | "revoked" | "expired"; mode: SourceMode }
export interface ActionItem { id: string; type: string; target: string | null; status: "pending" | "executed" | "reverted" | "failed"; incident_id: number | null; created_at: string | null; reversible: boolean; mode: SourceMode }
export interface Protection { id: string; name: string; sensor: string; description: string | null; mode: SourceMode; mitre: MitreTechnique[] }
export interface LabScenario { id: string; name: string; control: string; description: string | null; event_source: string | null; mode: SourceMode; mitre: MitreTechnique[] }
