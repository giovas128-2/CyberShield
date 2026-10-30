/* Servicio de Dispositivos, Sesiones, Acciones, Protecciones y Laboratorio (D4, frontend desacoplado).
   NO hace peticiones de red: devuelve los datos de src/mocks/mockData.ts marcados como source:"mock" (las pantallas muestran "DATOS SIMULADOS").
   Giss: reemplaza el cuerpo de cada getXxx por la lectura real del backend y devuelve { data, source: "api" }.
   Si el JSON real nombra distinto algún campo, normalízalo aquí (los tipos de salida están en src/types/index.ts). */
import { MOCK_ACTIONS, MOCK_DEVICES, MOCK_PROTECTIONS, MOCK_SCENARIOS, MOCK_SESSIONS } from "../mocks/mockData";

export type Source = "api" | "mock";
export interface Loaded<T> { data: T; source: Source; reason?: string }

const REASON = "Frontend desacoplado: datos del mock local (src/mocks/mockData.ts)";
const wait = (ms = 120) => new Promise<void>((r) => setTimeout(r, ms));
async function fromMock<T>(mock: T[]): Promise<Loaded<T[]>> {
  await wait();
  return { data: JSON.parse(JSON.stringify(mock)) as T[], source: "mock", reason: REASON };
}

/* BACKEND_GISS: getDevices <- dispositivos del backend: device.{id, device_name|name, user, platform|os, status (trusted|untrusted|revoked), last_seen, source_mode} */
export const getDevices = (_s?: AbortSignal) => fromMock(MOCK_DEVICES);
/* BACKEND_GISS: getSessions <- sesiones del backend: session.{id, user, device, ip, started_at, status (active|revoked|expired), source_mode} */
export const getSessions = (_s?: AbortSignal) => fromMock(MOCK_SESSIONS);
/* BACKEND_GISS: getActions <- acciones de respuesta: action.{id, action_type|type, target, status (executed|rolled_back|failed|pending), incident_id, created_at, reversible, source_mode} */
export const getActions = (_s?: AbortSignal) => fromMock(MOCK_ACTIONS);
/* BACKEND_GISS: getProtections <- controles de protección: control.{id, name, sensor, description, source_mode (integrated|simulated|pending), mitre_techniques[]} */
export const getProtections = (_s?: AbortSignal) => fromMock(MOCK_PROTECTIONS);
/* BACKEND_GISS: getLabScenarios <- escenarios de laboratorio: scenario.{id, name, control, description, event_source, source_mode, mitre_techniques[]} */
export const getLabScenarios = (_s?: AbortSignal) => fromMock(MOCK_SCENARIOS);
