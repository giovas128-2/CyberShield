/* Acceso a la EVIDENCIA (D4). Los datos de ejemplo viven en el mock central (src/mocks/mockData.ts §10); aquí solo está el punto único de lectura.
   El id del incidente sale de la ruta (no está escrito aquí). Este archivo NO hace fetch/axios/WebSocket.
   Giss reemplaza getEvidenceResult() por la respuesta real del backend (ver README_INTEGRACION_GISS.md).
   Convención: BACKEND_GISS: <variable visual> <- <dato backend esperado> */
import type { EvidenceAttack, EvidenceResult, EvidenceScenario } from "../types/evidence";
import { adaptEvidencePayload } from "../components/evidence/adaptEvidence";
import { buildMockEvidencePayload } from "./mockData";

export const EVIDENCE_ATTACKS: { key: EvidenceAttack; label: string }[] = [
  { key: "brute_force", label: "Fuerza bruta" }, { key: "ransomware", label: "Ransomware-like (simulación)" },
];
export const EVIDENCE_SCENARIOS: { key: EvidenceScenario; label: string }[] = [
  { key: "detected", label: "1 · Detectado" }, { key: "responding", label: "2 · Respondiendo" }, { key: "contained", label: "3 · Contenido" },
  { key: "failed", label: "Fallido" }, { key: "escalated", label: "Escalado" },
];
/* Simulaciones de errores de API (solo mock) para ver cómo reacciona la pantalla. */
export const EVIDENCE_SIMULATIONS: { key: string; label: string }[] = [
  { key: "cargando", label: "Cargando" }, { key: "vacio", label: "Sin evidencia (404)" }, { key: "error", label: "Error de API (500)" }, { key: "invalido", label: "Payload inválido" },
];

/* "7" / "inc-7" -> "INC-007" (solo normaliza el texto de la ruta). */
export const normalizeIncidentCode = (id: string) => { const m = /(\d+)$/.exec(id); return m ? `INC-${m[1].padStart(3, "0")}` : id.toUpperCase(); };
const SCENARIOS: EvidenceScenario[] = ["detected", "responding", "contained", "failed", "escalated"];
export const parseScenario = (v: string | null): EvidenceScenario | null => (SCENARIOS.find((s) => s === v) ?? null);
export const parseAttack = (v: string | null): EvidenceAttack => (v === "ransomware" ? "ransomware" : "brute_force");

/* BACKEND_GISS: REEMPLAZAR esta función por la lectura real de la evidencia del incidente `incidentId` (contrato de César/Sebas):
     1) pedir el JSON al servicio real  2) `adaptEvidencePayload(json)`  3) devolver {phase:"ready", ev} | {phase:"empty"} | {phase:"error"}.
   Mientras tanto devuelve el mock local. `estado` y `ataque` son solo del mock (?estado=...&ataque=...), el backend real los ignora:
   con backend real el tipo de ataque lo dicta event_type y el estado lo dicta status. */
export function getEvidenceResult(incidentId: string, estado: string | null, ataque: string | null = null): EvidenceResult {
  const id = normalizeIncidentCode(incidentId);
  if (!incidentId.trim()) return { phase: "empty", incident_id: "—" };
  if (estado === "cargando") return { phase: "loading" };
  if (estado === "vacio") return { phase: "empty", incident_id: id };
  if (estado === "error") return { phase: "error", code: "HTTP_500", message: "El servicio de evidencia no respondió correctamente." };
  if (estado === "invalido") { const ev = adaptEvidencePayload({ status: "CONTAINED" }); return ev ? { phase: "ready", ev } : { phase: "error", code: "PAYLOAD_INVALIDO", message: "La respuesta del backend no trae incident_id; no se puede mostrar la evidencia." }; }
  const ev = adaptEvidencePayload(buildMockEvidencePayload(id, parseAttack(ataque), parseScenario(estado) ?? "contained"));
  return ev ? { phase: "ready", ev } : { phase: "error", code: "PAYLOAD_INVALIDO", message: "No se pudo interpretar la evidencia." };
}
