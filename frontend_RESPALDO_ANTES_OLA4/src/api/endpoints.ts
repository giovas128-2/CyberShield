/* ===== RUTAS PENDIENTES DE CONFIRMAR CON CÉSAR =====
   No están definidas en el contrato del backend, por eso valen null (el frontend NO inventa rutas).
   Mientras sean null, cada pantalla muestra datos de src/mocks con el aviso "DATOS SIMULADOS".
   Cuando César confirme una ruta, pégala aquí (ej.: devices: "/devices") y ajusta el normalizador en src/services/management.ts. */
export const PENDING_ENDPOINTS: Record<"devices" | "sessions" | "actions" | "protections" | "labScenarios", string | null> = {
  devices: "/devices",
  sessions: "/sessions",
  actions: "/response-actions",
  protections: "/protections",
  labScenarios: "/lab/scenarios",
};
// POST para ejecutar un escenario de laboratorio. Pendiente de contrato.
export const LAB_RUN_ENDPOINT: string | null = "/lab/scenarios";
