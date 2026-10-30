# ENTREGA_D4 · Jacobo · Frontend desacoplado · Evidencia y respuesta real
**Resultado: PARCIAL** — el código y la documentación están completos y revisados, pero en mi entorno **no pude ejecutar `npm install` ni `npm run build`** (la red del sandbox bloquea el registro de npm). Falta correr el build y revisar la consola en tu máquina (pasos abajo). No se marca APROBADO sin esa validación y sin QA de integración.

Paquete: `D4_Jacobo_CyberShield.zip` · Base: D3 (`D3_Jacobo_CyberShield`) · Sin `node_modules`, `dist` ni `.env`.

## 1. Archivos
**Creados (3)**
| Archivo | Para qué sirve |
|---|---|
| `src/mocks/mockData.ts` | **Mock central único**: usuario, servidores, eventos, incidentes, dashboard, estadísticas, notificaciones, dispositivos/sesiones/acciones/protecciones/laboratorio, EmpresaDemo y el generador de evidencia (2 ataques × 5 estados). Un comentario `BACKEND_GISS` por grupo de campos. |
| `README_INTEGRACION_GISS.md` | Qué copiar, dependencias, componente raíz, dónde está el mock, variables y pasos exactos para reemplazar el mock. |
| `CAMBIOS_D4.diff` | Diff exacto contra D3 (para rollback). |

**Reescritos / modificados**
| Archivo | Cambio |
|---|---|
| `src/api/client.ts` | Sin axios/red: mismas funciones y firmas, devuelven el mock (con espera simulada). `BACKEND_GISS` en cada función. Agrega `runLabScenario`. |
| `src/services/management.ts` | Sin red: devuelve mocks con `source:"mock"`. |
| `src/hooks/useCyberShieldData.ts` | `MOCK_MODE = true` (la app se marca como "DATOS SIMULADOS"); sin importar mocks sueltos. |
| `src/mocks/evidenceMock.ts` | Solo queda el punto único de lectura `getEvidenceResult`; los datos pasaron a `mockData.ts`. |
| `src/empresademo/fixtures.ts` | Solo helpers de sesión de la demo + re-exportación (datos en `mockData.ts`). |
| `src/pages/LabPage.tsx`, `Register.tsx`, `ServersView.tsx` | Quitan `api(...)`/rutas/`isNet`; textos sin mencionar backend/endpoint. |
| `SimBanner.tsx`, `OriginChip.tsx`, `EventsPage.tsx` | Solo texto del aviso de datos simulados. |
| Resto de páginas y componentes (`Dashboard*`, `Events`, `Incidents*`, `Notifications`, `Devices`, `Sessions`, `Actions`, `Protections`, `Login`, `Sidebar`, `ED*`, `EmpresaDemoLayout`) | Una línea de comentario `BACKEND_GISS` al inicio. Sin cambios de diseño. |
| `MAPEO_BACKEND_FRONTEND.md` | Sección D4 con variable ↔ dato backend de TODAS las pantallas. |
| `package.json`, `package-lock.json`, `frontend/README.md` | Se quita `axios`; README nuevo. |

**Eliminados:** `src/api/endpoints.ts`, `.env.example` (`VITE_API_URL`), `src/data/mock.ts`, `src/mocks/management.ts`, `src/layout/Console.tsx` (código muerto, no enrutado). **Movidos** a `frontend/docs_anteriores/`: los `INTEGRACION_*`, `FINAL_UI_QA_CESAR`, `DEMO_FLOW_CESAR` (historial). Reemplazados: `ENTREGA_D3.md` y `PASOS_PARA_GISS.md` → este archivo y `README_INTEGRACION_GISS.md`.

## 2. Probar desde cero
1. `cd frontend && npm install`
2. `npm run build` → debe terminar sin errores (**pendiente de correr**).
3. `npm run dev` y abrir `http://localhost:5173/#/login/cybershield`; entrar con cualquier correo válido y contraseña.
4. Recorrer: Dashboard, Eventos, Incidentes, Notificaciones, Acciones, Servidores, Laboratorio.
5. `#/incidents/INC-077/evidence?estado=contained` → fuerza bruta contenida (`BLOCK_SOURCE_IP`); luego `?estado=failed` y `?estado=escalated` (rojo/ámbar, nunca "Empresa protegida").
6. `#/incidents/INC-078/evidence?ataque=ransomware&estado=escalated` → mismo componente, otro ataque.
7. F5 en cada ruta de evidencia → mismo resultado. `#/empresa-demo/login` → flujo EmpresaDemo.
8. DevTools: Network sin peticiones a servidor; Console sin errores.

## 3. Evidencia
- Verificado por mí: `grep` sin `fetch`/`axios`/`endpoints`/`VITE_API_URL`/`import.meta.env` en `src/`; revisión de tipos con `tsc` (con módulos de terceros simulados) sin errores en el código del proyecto; **116 marcas `BACKEND_GISS` en 35 archivos**.
- **No verificado:** build real de Vite, consola del navegador, responsive/proyector tras estos cambios.
- `capturas/` contiene las capturas de **D3** (contained / failed / escalated, 1366×768 y 1920×1080). La interfaz de evidencia no cambió en D4, pero **no son capturas nuevas**: vuelve a tomarlas tras el build si las vas a presentar como D4.

## 4. Checklist
☐ Build sin errores — **pendiente (no ejecutable aquí)**
☐ Sin console errors en ruta demo — **pendiente**
☐ Responsive/proyector correcto — **pendiente** (sin cambios de CSS respecto a D3)
☑ No hay placeholders visibles — el único texto entre corchetes es `[command_preview · lo entrega el backend…]` del ransomware, **intencional** (no se inventa un comando); la franja "DATOS SIMULADOS" es deliberada.
☑ Sin red en `src/`; mock en un solo archivo; `BACKEND_GISS` en todo dato dinámico.

## 5. Rollback
Volver a `D3_Jacobo_CyberShield.zip`, o desde este paquete: `patch -R -p1 < CAMBIOS_D4.diff` (ejecutado en la raíz del paquete).

## 6. Bloqueos y dependencia para mañana
- Bloqueo: no se pudo compilar en el sandbox (npm sin acceso). `07_evidence_payload_example.json` no venía en el material; el contrato salió del Plan Maestro y del mock.
- Dependencia: Giss conecta el JSON real en `EvidencePage.tsx` + `adaptEvidence.ts` y reemplaza las funciones de `client.ts`; Jacobo corre el build local y reenvía capturas nuevas si aparece algún error.
