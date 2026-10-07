import type { Evento, Incidente } from "../types";

const ago = (minutes: number) => new Date(Date.now() - minutes * 60000).toISOString();

export const MOCK_EVENTS: Evento[] = [
  { id: 1, fecha: "12:01", createdAt: ago(8), tipo: "Login correcto", origen: "192.168.1.10", severidad: "BAJA", estado: "Registrado" },
  { id: 2, fecha: "12:03", createdAt: ago(6), tipo: "Intentos fallidos", origen: "192.168.1.50", severidad: "ALTA", estado: "Detectado" },
  { id: 3, fecha: "12:04", createdAt: ago(4), tipo: "Tráfico sospechoso", origen: "192.168.1.80", severidad: "MEDIA", estado: "Detectado" },
  { id: 4, fecha: "12:05", createdAt: ago(2), tipo: "Servicio reiniciado", origen: "192.168.1.10", severidad: "BAJA", estado: "Registrado" },
];

export const MOCK_INC: Incidente[] = [
  {
    id: "INC-003",
    backendId: 3,
    eventType: "multiple_login_attempts",
    titulo: "Múltiples intentos de autenticación",
    resumen: "18 intentos de autenticación en una ventana corta de tiempo.",
    severidad: "ALTA",
    estado: "Investigando",
    status: "investigating",
    origen: "192.168.1.50",
    servidor: "srv-cyber-01",
    servicio: "Autenticación",
    detectado: "02 oct 2026 · 12:03",
    asignado: "César",
    regla: "AUTH-FAIL-MVP",
    reco: "Verifica si el origen está autorizado y revisa los registros de autenticación antes de cerrar la alerta.",
    investigationSteps: [
      "Identificar la IP de origen.",
      "Revisar el usuario afectado.",
      "Comprobar la cantidad de intentos y la ventana de tiempo.",
    ],
    resolutionCriteria: "La actividad fue validada como legítima o se aplicó una mitigación autorizada.",
  },
  {
    id: "INC-002",
    backendId: 2,
    eventType: "suspicious_network_traffic",
    titulo: "Tráfico de red sospechoso",
    resumen: "Se detectó un patrón de tráfico que requiere revisión.",
    severidad: "MEDIA",
    estado: "Pendiente",
    status: "open",
    origen: "192.168.1.80",
    servidor: "srv-cyber-01",
    servicio: "Red",
    detectado: "02 oct 2026 · 12:04",
    asignado: "—",
    regla: "NETWORK-MVP",
    reco: "Valida si el destino y el servicio forman parte de la operación normal.",
    investigationSteps: [
      "Revisar IP de origen y destino.",
      "Identificar puertos y protocolo.",
      "Comprobar frecuencia y duración del tráfico.",
    ],
    resolutionCriteria: "El tráfico fue validado como esperado o se aplicó una mitigación autorizada.",
  },
];
