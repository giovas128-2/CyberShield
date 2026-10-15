import type { Evento, Incidente } from "../types";

const ago = (minutes: number) => new Date(Date.now() - minutes * 60000).toISOString();

export const MOCK_EVENTS: Evento[] = [
  { id: 1, fecha: "12:01", createdAt: ago(8), tipo: "authentication_failure", origen: "192.168.1.10", severidad: "NORMAL", estado: "Registrado", scope: "BLOCKED", serverId: 2 },
  { id: 2, fecha: "12:03", createdAt: ago(6), tipo: "authentication_burst", origen: "192.168.1.50", severidad: "HIGH", estado: "Detectado", scope: "REACHED", serverId: 2 },
  { id: 3, fecha: "12:04", createdAt: ago(4), tipo: "suspicious_network_traffic", origen: "192.168.1.80", severidad: "WARNING", estado: "Registrado", scope: "REACHED", serverId: 2 },
  { id: 4, fecha: "12:05", createdAt: ago(2), tipo: "privilege_escalation", origen: "192.168.1.90", severidad: "CRITICAL", estado: "Detectado", scope: "IMPACT", serverId: 2 },
];

export const MOCK_INC: Incidente[] = [
  {
    id: "INC-003", backendId: 3, eventType: "authentication_burst",
    titulo: "Patrón sospechoso de autenticación",
    resumen: "Actividad de autenticación contra varias cuentas en una ventana corta.",
    severidad: "HIGH", estado: "Investigando", status: "investigating",
    origen: "192.168.1.50", servidor: "srv-cyber-01", servicio: "Autenticación",
    detectado: "14 oct 2026 · 12:03", asignado: "César", regla: "AUTH-CORRELATION",
    reco: "Validar el origen, las cuentas afectadas y si hubo acceso exitoso posterior.",
    investigationSteps: ["Revisar origen y cuentas afectadas.", "Correlacionar fallos y accesos exitosos.", "Buscar actividad privilegiada posterior."],
    resolutionCriteria: "La actividad quedó explicada o contenida con evidencia suficiente.",
  },
];
