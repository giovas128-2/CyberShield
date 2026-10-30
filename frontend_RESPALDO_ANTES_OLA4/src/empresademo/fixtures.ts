/* EmpresaDemo: aplicación corporativa FICTICIA protegida por CyberShield.
   Todos los datos son inventados (sin personas, correos, teléfonos ni credenciales reales). No hay llamadas al backend. */

export const ED_DATE_LABEL = "Martes, 20 de octubre de 2026";
export const ED_ORIGIN = "ORIGEN: DEMO · 20 oct 2026 · 10:24 UTC";

export interface EDDevice { name: string; id: string; trusted: boolean }
export const ED_DEVICES: Record<string, EDDevice> = {
  "demo-equipo-01": { name: "demo-equipo-01", id: "DV-001", trusted: true },
  "demo-equipo-06": { name: "demo-equipo-06", id: "DV-006", trusted: false },
};
export const ED_PROFILE = { alias: "Analista Demo", user: "analista.demo", org: "Oficina central ficticia", role: "Analista de muestra", session: "SES-011" };

const KEY = "ed_device";
/* Sesión de demostración: solo recuerda qué equipo ficticio se eligió; no es autenticación real. */
export const edGetDevice = (): EDDevice | null => { try { const k = sessionStorage.getItem(KEY); return k ? ED_DEVICES[k] ?? null : null; } catch { return null; } };
export const edSetDevice = (name: string) => { try { sessionStorage.setItem(KEY, name); } catch { /* sin almacenamiento: la demo sigue funcionando */ } };
export const edClear = () => { try { sessionStorage.removeItem(KEY); } catch { /* noop */ } };

export interface EDClient { id: string; code: string; name: string; sector: string; owner: string; status: "En curso" | "En revisión" | "En seguimiento"; last: string; note: string }
export const ED_CLIENTS: EDClient[] = [
  { id: "c1", code: "CLI-001", name: "Proyecto Olivo", sector: "Servicios profesionales", owner: "Equipo Demo A", status: "En curso", last: "Hoy · Propuesta v3", note: "Relación activa desde septiembre de 2026. Propuesta comercial DOC-018 actualizada hoy a las 10:08. Próximo hito ficticio: revisión de alcance." },
  { id: "c2", code: "CLI-002", name: "Estudio Bruma", sector: "Diseño y consultoría", owner: "Equipo Demo B", status: "En curso", last: "Hoy · Resumen revisado", note: "Resumen de servicio DOC-016 revisado esta mañana. Sin pendientes críticos." },
  { id: "c3", code: "CLI-003", name: "Grupo Ladera", sector: "Operaciones", owner: "Equipo Demo A", status: "En revisión", last: "19 oct · Plan de trabajo", note: "Plan de trabajo DOC-012 en borrador, pendiente de revisión del equipo." },
  { id: "c4", code: "CLI-004", name: "Taller Marea", sector: "Producción", owner: "Equipo Demo C", status: "En curso", last: "18 oct · Entrega de muestra", note: "Entrega de muestra DOC-011 revisada." },
  { id: "c5", code: "CLI-005", name: "Casa Umbral", sector: "Comercio", owner: "Equipo Demo B", status: "En seguimiento", last: "17 oct · Nota de proyecto", note: "Nota de proyecto DOC-009 por revisar." },
  { id: "c6", code: "CLI-006", name: "Nodo Prado", sector: "Tecnología", owner: "Equipo Demo C", status: "En curso", last: "16 oct · Reporte mensual", note: "Reporte mensual compartido con el equipo." },
];

export interface EDDoc { id: string; code: string; title: string; kind: string; client: string; state: "Por revisar" | "Revisado" | "Borrador"; version: string; when: string; owner: string; outline: string[] }
export const ED_DOCS: EDDoc[] = [
  { id: "d1", code: "DOC-018", title: "Propuesta comercial", kind: "Documento", client: "Proyecto Olivo", state: "Por revisar", version: "v3", when: "Hoy · 10:08", owner: "Equipo Demo A", outline: ["Objetivo del proyecto", "Alcance orientativo", "Próximos pasos"] },
  { id: "d2", code: "DOC-016", title: "Resumen de servicio", kind: "Documento", client: "Estudio Bruma", state: "Revisado", version: "v2", when: "Hoy · 09:42", owner: "Equipo Demo B", outline: ["Contexto", "Servicios entregados", "Siguientes pasos"] },
  { id: "d3", code: "DOC-012", title: "Plan de trabajo", kind: "Documento", client: "Grupo Ladera", state: "Borrador", version: "v1", when: "Ayer", owner: "Equipo Demo A", outline: ["Etapas", "Responsables ficticios", "Calendario de muestra"] },
  { id: "d4", code: "DOC-011", title: "Entrega de muestra", kind: "Documento", client: "Taller Marea", state: "Revisado", version: "v2", when: "18 oct", owner: "Equipo Demo C", outline: ["Resumen", "Entregables", "Observaciones"] },
  { id: "d5", code: "DOC-009", title: "Nota de proyecto", kind: "Nota", client: "Casa Umbral", state: "Por revisar", version: "v1", when: "17 oct", owner: "Equipo Demo B", outline: ["Contexto", "Notas"] },
];

export const ED_ACTIVITY = [
  { t: "10:08", title: "Propuesta actualizada", meta: "DOC-018 · Proyecto Olivo · Versión 3" },
  { t: "09:42", title: "Documento revisado", meta: "DOC-016 · Estudio Bruma" },
  { t: "09:30", title: "Reporte consultado", meta: "REP-006 · Resumen de octubre" },
  { t: "09:00", title: "Acceso normal", meta: "Analista Demo · Equipo de confianza" },
];
export const ED_REPORTS = [
  { code: "REP-006", name: "Resumen de octubre", period: "Octubre 2026", content: "Actividad del equipo", last: "Hoy · 09:30" },
  { code: "REP-005", name: "Seguimiento documental", period: "Octubre 2026", content: "Versiones y revisiones", last: "19 oct · 15:20" },
  { code: "REP-004", name: "Panorama de clientes", period: "Septiembre 2026", content: "Relaciones y proyectos", last: "17 oct · 11:05" },
];
/* Distribución ilustrativa del 1 al 20 de octubre; no representa productividad real. */
export const ED_BARS = [5, 9, 6, 12, 8, 10, 19, 38, 15, 8, 6, 5];
