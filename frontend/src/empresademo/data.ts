/* Datos FICTICIOS de EmpresaDemo para las interfaces normales 01-07. Sin backend ni datos personales reales. */
export const ED_USER = { initials: "LM", name: "Lucía Méndez", role: "Gestora de operaciones", email: "lucia.mendez@empresademo.test" };
export const ED_ADMIN = { initials: "MS", name: "Mateo Salas", role: "Administrador" };
export const ED_FOOT_DATE = "30 oct 2026 · ES";

export const DEMO_KPIS = [
  { label: "Clientes activos", value: "248", hint: "18 altas este mes · muestra ficticia" },
  { label: "Documentos vigentes", value: "1.284", hint: "96 % con revisión actualizada" },
  { label: "Reportes del mes", value: "32", hint: "8 listos para consulta" },
  { label: "Tareas pendientes", value: "12", hint: "4 requieren tu revisión" },
];

export const DEMO_ACTIVITY = [
  { what: "Ficha de Lumen actualizada", who: "Lucía Méndez", when: "Hoy · 09:42" },
  { what: "Informe comercial consultado", who: "Diego Ríos", when: "Hoy · 09:25" },
  { what: "Contrato sintético revisado", who: "Elena Torres", when: "Hoy · 09:10" },
  { what: "Cliente Nova registrado", who: "Lucía Méndez", when: "Ayer · 16:30" },
];

export interface DemoClient {
  id: string; code: string; name: string; sector: string; status: "Activo" | "En revisión" | "Inactivo";
  owner: string; ownerFull: string; last: string; contact: string; alta: string;
  docs: { name: string; state: string }[]; activity: { t: string; text: string }[];
}
export const DEMO_CLIENTS: DemoClient[] = [
  { id: "c1", code: "CLI-DEMO-024", name: "Lumen Servicios", sector: "Sector servicios", status: "Activo", owner: "Lucía M.", ownerFull: "Lucía Méndez", last: "Hoy · 09:42", contact: "lumen@ejemplo.test", alta: "12 sep 2026",
    docs: [{ name: "Contrato_DEMO.pdf", state: "Vigente" }, { name: "Ficha_comercial_DEMO.pdf", state: "Revisada" }], activity: [{ t: "09:42", text: "Actualización de contacto" }, { t: "09:30", text: "Consulta de ficha" }] },
  { id: "c2", code: "CLI-DEMO-025", name: "Nova Industrial", sector: "Sector industria", status: "Activo", owner: "Diego R.", ownerFull: "Diego Ríos", last: "Hoy · 09:18", contact: "nova@ejemplo.test", alta: "03 sep 2026",
    docs: [{ name: "Presupuesto_DEMO.xlsx", state: "Vigente" }], activity: [{ t: "09:18", text: "Consulta de ficha" }] },
  { id: "c3", code: "CLI-DEMO-026", name: "Atlas Consultoría", sector: "Sector consultoría", status: "En revisión", owner: "Elena T.", ownerFull: "Elena Torres", last: "Ayer · 17:30", contact: "atlas@ejemplo.test", alta: "21 ago 2026",
    docs: [{ name: "Manual_DEMO.pdf", state: "En revisión" }], activity: [{ t: "Ayer 17:30", text: "Revisión de ficha" }] },
  { id: "c4", code: "CLI-DEMO-027", name: "Brisa Comercial", sector: "Sector comercio", status: "Activo", owner: "Lucía M.", ownerFull: "Lucía Méndez", last: "Ayer · 14:05", contact: "brisa@ejemplo.test", alta: "15 ago 2026",
    docs: [{ name: "Ficha_DEMO.docx", state: "Vigente" }], activity: [{ t: "Ayer 14:05", text: "Consulta de ficha" }] },
  { id: "c5", code: "CLI-DEMO-028", name: "Nexo Logística", sector: "Sector logística", status: "Inactivo", owner: "Diego R.", ownerFull: "Diego Ríos", last: "27 oct · 11:40", contact: "nexo@ejemplo.test", alta: "02 jul 2026",
    docs: [], activity: [{ t: "27 oct 11:40", text: "Cambio de estado" }] },
  { id: "c6", code: "CLI-DEMO-029", name: "Faro Gestión", sector: "Sector gestión", status: "Activo", owner: "Elena T.", ownerFull: "Elena Torres", last: "26 oct · 10:22", contact: "faro@ejemplo.test", alta: "30 jun 2026",
    docs: [{ name: "Política_DEMO.pdf", state: "Vigente" }], activity: [{ t: "26 oct 10:22", text: "Consulta de ficha" }] },
];

export interface DemoDoc { name: string; type: string; area: string; level: "Confidencial" | "Restringido" | "Interno"; owner: string; date: string; state: "Vigente" | "En revisión" }
export const DEMO_DOCS: DemoDoc[] = [
  { name: "Contrato_DEMO.pdf", type: "PDF", area: "Comercial", level: "Confidencial", owner: "Lucía Méndez", date: "29 oct 2026", state: "Vigente" },
  { name: "Presupuesto_DEMO.xlsx", type: "XLSX", area: "Finanzas", level: "Restringido", owner: "Diego Ríos", date: "28 oct 2026", state: "Vigente" },
  { name: "Manual_DEMO.pdf", type: "PDF", area: "Operaciones", level: "Interno", owner: "Elena Torres", date: "27 oct 2026", state: "En revisión" },
  { name: "Ficha_DEMO.docx", type: "DOCX", area: "Comercial", level: "Interno", owner: "Lucía Méndez", date: "26 oct 2026", state: "Vigente" },
  { name: "Política_DEMO.pdf", type: "PDF", area: "Personas", level: "Interno", owner: "Elena Torres", date: "25 oct 2026", state: "Vigente" },
];

export interface DemoReport { name: string; date: string; area: string; owner: string; state: "Listo" | "Borrador" }
export const DEMO_REPORTS: DemoReport[] = [
  { name: "Resumen comercial", date: "30 oct 2026", area: "Comercial", owner: "Lucía Méndez", state: "Listo" },
  { name: "Balance de operaciones", date: "29 oct 2026", area: "Operaciones", owner: "Elena Torres", state: "Listo" },
  { name: "Seguimiento de cartera", date: "28 oct 2026", area: "Finanzas", owner: "Diego Ríos", state: "Listo" },
  { name: "Indicadores de servicio", date: "27 oct 2026", area: "Operaciones", owner: "Elena Torres", state: "Borrador" },
];
export const DEMO_EXPORTS = [
  { file: "Comercial_oct_DEMO.csv", who: "Lucía Méndez", dest: "Descarga corporativa", when: "Hoy · 09:20", result: "Completada" },
  { file: "Operación_DEMO.pdf", who: "Elena Torres", dest: "Carpeta interna", when: "Ayer · 16:15", result: "Completada" },
  { file: "Cartera_DEMO.csv", who: "Diego Ríos", dest: "Descarga corporativa", when: "Ayer · 11:05", result: "Completada" },
];

export const DEMO_ROLE_PERMS: [string, string][] = [
  ["Clientes", "Consultar y editar"], ["Documentos", "Consultar y gestionar"], ["Reportes", "Consultar y exportar"], ["Administración", "No autorizado"],
];
export const DEMO_SESSIONS = [
  { device: "Portátil corporativo · Chrome", place: "Sede central", last: "Hoy · 09:02", state: "Actual · Reconocido", action: "Esta sesión" },
  { device: "Equipo de oficina · Edge", place: "Sede central", last: "Ayer · 17:35", state: "Reconocido", action: "Cerrar sesión" },
  { device: "Portátil corporativo · Chrome", place: "Sede central", last: "28 oct · 08:55", state: "Cerrada", action: "Consultar" },
];

export const DEMO_ORG_SETTINGS = [
  { setting: "Organización", value: "EmpresaDemo", action: "Editar configuración" },
  { setting: "Política de sesión", value: "Reautenticación sensible", action: "Revisar" },
  { setting: "Recursos internos", value: "3 grupos de acceso", action: "Gestionar" },
];
export const DEMO_SENSITIVE = ["Repositorio financiero", "Gestión de usuarios", "Configuración interna"];
export const DEMO_USERS = [
  { name: "Mateo Salas", area: "Tecnología", role: "Administrador", state: "Activo" },
  { name: "Lucía Méndez", area: "Operaciones", role: "Gestora", state: "Activo" },
  { name: "Diego Ríos", area: "Finanzas", role: "Analista", state: "Activo" },
  { name: "Elena Torres", area: "Operaciones", role: "Supervisora", state: "Activo" },
];
