/* DATOS SIMULADOS de Dispositivos, Sesiones, Acciones, Protecciones y Laboratorio.
   Se reemplazan cuando exista el endpoint real (ver src/api/endpoints.ts). Los mapeos MITRE son de demostración:
   deben ser revisados por el responsable de ciberseguridad antes de presentarse como reales. */
import type { ActionItem, Device, LabScenario, MitreTechnique, Protection, SessionItem } from "../types";

const ago = (min: number) => new Date(Date.now() - min * 60000).toISOString();
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
  { id: "c2", name: "Dispositivo no autorizado", sensor: "Aplicación", description: null, mode: "integrated", mitre: [mt("T1078", "Valid Accounts", "Defense Evasion")] },
  { id: "c3", name: "Cambio de archivo crítico", sensor: "Wazuh FIM", description: null, mode: "integrated", mitre: [mt("T1565.001", "Stored Data Manipulation", "Impact")] },
  { id: "c4", name: "Abuso de privilegios", sensor: "Wazuh", description: null, mode: "integrated", mitre: [mt("T1548.003", "Sudo and Sudo Caching", "Privilege Escalation")] },
  { id: "c5", name: "Conexión externa sospechosa", sensor: "Suricata", description: null, mode: "integrated", mitre: [mt("T1041", "Exfiltration Over C2 Channel", "Exfiltration")] },
  { id: "c6", name: "Exfiltración de datos", sensor: "Suricata + App", description: null, mode: "integrated", mitre: [mt("T1041", "Exfiltration Over C2 Channel", "Exfiltration")] },
  { id: "c7", name: "Ransomware behavior", sensor: "Wazuh", description: null, mode: "simulated", mitre: [mt("T1486", "Data Encrypted for Impact", "Impact")] },
  { id: "c8", name: "Movimiento lateral", sensor: "Wazuh + Suricata", description: null, mode: "simulated", mitre: [mt("T1021.004", "Remote Services: SSH", "Lateral Movement")] },
];
export const MOCK_SCENARIOS: LabScenario[] = MOCK_PROTECTIONS.map((p, i) => ({
  id: `sc${i + 1}`, name: p.name, control: p.name, description: "Genera telemetría defensiva de prueba para validar detección, clasificación y respuesta.",
  event_source: p.sensor, mode: p.mode, mitre: p.mitre,
}));
