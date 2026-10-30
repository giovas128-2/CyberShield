/* EmpresaDemo: los DATOS ficticios viven en el mock central (src/mocks/mockData.ts §9). Aquí solo quedan los helpers de sesión de la demo
   y la re-exportación para que las páginas ED* no cambien sus imports. No hay llamadas al backend. */
import { ED_DEVICES, type EDDevice } from "../mocks/mockData";
export { ED_ACTIVITY, ED_BARS, ED_CLIENTS, ED_DATE_LABEL, ED_DEVICES, ED_DOCS, ED_ORIGIN, ED_PROFILE, ED_REPORTS } from "../mocks/mockData";
export type { EDClient, EDDevice, EDDoc } from "../mocks/mockData";

const KEY = "ed_device";
/* Sesión de demostración: solo recuerda qué equipo ficticio se eligió; no es autenticación real. */
export const edGetDevice = (): EDDevice | null => { try { const k = sessionStorage.getItem(KEY); return k ? ED_DEVICES[k] ?? null : null; } catch { return null; } };
export const edSetDevice = (name: string) => { try { sessionStorage.setItem(KEY, name); } catch { /* sin almacenamiento: la demo sigue funcionando */ } };
export const edClear = () => { try { sessionStorage.removeItem(KEY); } catch { /* noop */ } };
