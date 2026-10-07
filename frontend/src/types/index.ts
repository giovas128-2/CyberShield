export type Severidad = "BAJA" | "MEDIA" | "ALTA" | "CRITICA";
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
  eventos: number;
  incidentes: number;
  riesgo: number;
}

export interface User {
  id?: number;
  name: string;
  email?: string;
}
