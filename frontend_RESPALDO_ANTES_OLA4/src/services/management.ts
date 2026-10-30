import { api, isMissing, isNet, normalizeMitre } from "../api/client";
import { PENDING_ENDPOINTS as E } from "../api/endpoints";
import { MOCK_ACTIONS, MOCK_DEVICES, MOCK_PROTECTIONS, MOCK_SCENARIOS, MOCK_SESSIONS } from "../mocks/management";
import type { ActionItem, Device, LabScenario, Protection, SessionItem, SourceMode } from "../types";

export type Source = "api" | "mock";
export interface Loaded<T> { data: T; source: Source; reason?: string }

const pick = (o: any, ...k: string[]) => { for (const x of k) if (o?.[x] != null) return o[x]; return undefined; };
const modeOf = (v: unknown): SourceMode => {
  const mode = String(v ?? "").toLowerCase();
  if (mode.startsWith("pend")) return "pending";
  if (mode.startsWith("sim")) return "simulated";
  return "integrated";
};
const oneOf = <T extends string>(v: unknown, list: T[], fallback: T): T => (list.includes(String(v).toLowerCase() as T) ? (String(v).toLowerCase() as T) : fallback);

/* Carga una lista. Si la ruta aún es null / no existe / el backend no responde -> devuelve el mock marcado como source:"mock". */
async function loadList<T>(path: string | null, normalize: (r: any) => T, mock: T[], signal?: AbortSignal): Promise<Loaded<T[]>> {
  if (!path) return { data: mock, source: "mock", reason: "Endpoint pendiente de definir (src/api/endpoints.ts)" };
  try { return { data: (await api<any[]>(path, "GET", undefined, signal)).map(normalize), source: "api" }; }
  catch (e) {
    if (isMissing(e)) return { data: mock, source: "mock", reason: `GET ${path} aún no existe en el backend` };
    if (isNet(e)) return { data: mock, source: "mock", reason: "Backend sin conexión" };
    throw e;
  }
}

/* PROVISIONAL: normalizadores tolerantes. Ajustar con el JSON real. */
const nDevice = (r: any): Device => {
  const rawStatus = String(pick(r, "status") ?? "").toLowerCase();

  const status: Device["status"] =
    rawStatus === "trusted"
      ? "trusted"
      : rawStatus === "untrusted" || rawStatus === "revoked"
        ? "unauthorized"
        : "unknown";

  return {
    id: String(pick(r, "id") ?? ""),
    name: String(
      pick(r, "device_name", "name", "hostname", "device_uuid") ?? "—"
    ),
    user: pick(r, "user", "username") ?? null,
    os: pick(r, "platform", "os") ?? null,
    status,
    last_seen: pick(r, "last_seen") ?? null,
    mode: modeOf(pick(r, "source_mode", "mode")),
  };
};
const nSession = (r: any): SessionItem => ({
  id: String(pick(r, "id") ?? ""),

  user:
    pick(r, "user", "username") ??
    (pick(r, "user_id") != null
      ? `Usuario #${pick(r, "user_id")}`
      : "—"),

  device:
    pick(r, "device", "device_name") ??
    (pick(r, "device_id") != null
      ? `Dispositivo #${pick(r, "device_id")}`
      : null),

  ip: pick(r, "ip", "ip_address", "source_ip") ?? null,

  started_at:
    pick(r, "started_at", "created_at") ?? null,

  status: oneOf(
    pick(r, "status"),
    ["active", "revoked", "expired"],
    "active"
  ),

  mode: modeOf(pick(r, "source_mode", "mode")),
});
const nAction = (r: any): ActionItem => {
  const rawStatus = String(pick(r, "status") ?? "").toLowerCase();

  const status: ActionItem["status"] =
    rawStatus === "executed"
      ? "executed"
      : rawStatus === "rolled_back"
        ? "reverted"
        : rawStatus === "failed"
          ? "failed"
          : "pending";

  return {
    id: String(pick(r, "id") ?? ""),
    type: String(
      pick(r, "type", "action", "action_type") ?? "—"
    ),
    target: pick(r, "target") ?? null,
    status,
    incident_id: pick(r, "incident_id") ?? null,
    created_at: pick(r, "created_at") ?? null,
    reversible: pick(r, "reversible") !== false,
    mode: modeOf(pick(r, "source_mode", "mode")),
  };
};
const nProtection = (r: any): Protection => ({ id: String(pick(r, "id") ?? ""), name: String(pick(r, "name", "control") ?? "—"), sensor: String(pick(r, "sensor") ?? "—"), description: pick(r, "description") ?? null, mode: modeOf(pick(r, "source_mode", "mode")), mitre: normalizeMitre(pick(r, "mitre_techniques", "mitre")) });
const nScenario = (r: any): LabScenario => ({ id: String(pick(r, "id") ?? ""), name: String(pick(r, "name") ?? "—"), control: String(pick(r, "control", "control_name") ?? "—"), description: pick(r, "description") ?? null,
  event_source: pick(r, "event_source", "source") ?? null, mode: modeOf(pick(r, "source_mode", "mode")), mitre: normalizeMitre(pick(r, "mitre_techniques", "mitre")) });

export const getDevices = (s?: AbortSignal) => loadList(E.devices, nDevice, MOCK_DEVICES, s);
export const getSessions = (s?: AbortSignal) => loadList(E.sessions, nSession, MOCK_SESSIONS, s);
export const getActions = (s?: AbortSignal) => loadList(E.actions, nAction, MOCK_ACTIONS, s);
export const getProtections = (s?: AbortSignal) => loadList(E.protections, nProtection, MOCK_PROTECTIONS, s);
export const getLabScenarios = (s?: AbortSignal) => loadList(E.labScenarios, nScenario, MOCK_SCENARIOS, s);
