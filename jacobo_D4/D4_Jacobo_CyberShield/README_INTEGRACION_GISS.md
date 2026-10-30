# README_INTEGRACION_GISS · D4 · Frontend desacoplado de CyberShield (Jacobo)

**Estado:** el frontend corre 100 % con mock local. No hay `fetch`, `axios`, `WebSocket`, URLs ni endpoints en `src/`. Nada depende del backend.
**Tú (Giss) eres quien integra.** Esta guía te dice qué copiar, dónde está el mock, qué variable va con qué dato y cómo reemplazarlo.

## 1. Cómo arrancar el frontend solo (para ver la referencia visual)
```bash
cd frontend
npm install
npm run dev        # o: npm run build && npm run preview
```
Sesión: cualquier correo válido y contraseña (el mock acepta todo). Todo el sistema muestra "DATOS SIMULADOS" mientras `MOCK_MODE = true`.

## 2. Dependencias npm
Solo las de siempre: `react`, `react-dom`, `react-router-dom`, `lucide-react` (y dev: `typescript`, `vite`, `@vitejs/plugin-react`, `@types/react`, `@types/react-dom`).
**No hay dependencias nuevas.** Se quitó `axios` de este paquete (el proyecto maestro conserva el suyo).

## 3. Componente raíz y rutas
- Raíz de la app: `src/App.tsx` (HashRouter). Layout con datos: `src/layout/AppLayout.tsx` (usa `useCyberShieldData`).
- **Pantallas de evidencia (lo central de la demo):** ruta `/incidents/:id/evidence` → `src/pages/EvidencePage.tsx` → `DetectionPanel` (pantalla 1) + `DefensiveCommandPanel` (pantalla 2) en `src/components/evidence/`. **Un solo componente para todos los ataques**; solo cambia el JSON.
- EmpresaDemo (app ficticia protegida): rutas `/empresa-demo/*`, carpeta `src/empresademo/` y `src/pages/empresademo/`.

## 4. Dónde está el mock (UN solo archivo)
`src/mocks/mockData.ts` — todo dato de ejemplo vive ahí, dividido en secciones numeradas:
1 usuario · 2 servidores · 3 eventos · 4 incidentes · 5 resumen dashboard · 6 estadísticas 1s/60s · 7 notificaciones · 8 dispositivos/sesiones/acciones/protecciones/laboratorio · 9 EmpresaDemo · 10 evidencia (generador del JSON de ejemplo de los 2 ataques × 5 estados).
Ningún componente tiene datos propios. Los comandos defensivos tampoco viven en componentes: salen de `response.command_preview` / `terminal_lines`.

## 5. Qué archivos copiar al proyecto maestro
| Copia (UI, sin lógica de datos) | Notas |
|---|---|
| `src/components/evidence/*` (DetectionPanel, DefensiveCommandPanel, adaptEvidence, evidenceUtils, MockStateSwitcher) | núcleo de la evidencia |
| `src/types/evidence.ts` | contrato del JSON de evidencia |
| `src/pages/EvidencePage.tsx` | **aquí conectas el servicio real** (ver §6.A) |
| `src/styles/styles.css` | estilos `.ev-*` (copia o fusiona; no cambia el resto) |
| `src/pages/IncidentDetailPage.tsx`, `IncidentsView.tsx`, `IncidentsPage.tsx` | si en el maestro aún no traen el botón/ruta de evidencia |
| `src/components/{SeverityBadge,SimBanner,OriginChip,Sidebar}.tsx`, `src/components/mitre/*` | si difieren del maestro |
| `src/empresademo/*`, `src/pages/empresademo/*` | si el maestro aún no tiene EmpresaDemo (los datos ED_* salen del mock) |
| `src/mocks/*` | opcional: sirve como fixture de desarrollo/regresión visual |

**NO sobrescribas** en el maestro: `src/api/client.ts`, `src/services/management.ts`, `src/hooks/useCyberShieldData.ts`. En este paquete son **simulaciones sin red** con la **misma firma** que el cliente real; sirven como especificación de qué función devuelve qué.

## 6. Pasos exactos para reemplazar el mock por el backend
### A. Evidencia (lo prioritario)
1. En `src/pages/EvidencePage.tsx` busca la línea marcada `BACKEND_GISS` donde se llama `getEvidenceResult(id, estado, ataque)`.
2. Reemplázala por: pedir el JSON de evidencia del incidente `id` → `adaptEvidencePayload(raw)` → `setResult({phase:"ready", ev})`. Estados ya dibujados: `loading | ready | empty | error` (el botón **Reintentar** debe volver a llamar tu función de carga). Mientras `ev.status` sea `DETECTED` o `RESPONDING` repite la lectura cada 2–3 s y detén el polling en `CONTAINED/FAILED/ESCALATED`.
3. Si el JSON real nombra distinto un campo, cámbialo **solo** en `src/components/evidence/adaptEvidence.ts` (una línea por campo). No lanza errores: lo que falta cae a un fallback (ver tabla en MAPEO).
4. Borra lo solo-dev: `<MockStateSwitcher …/>` en `EvidencePage.tsx` y la etiqueta `MOCK LOCAL` (`.ev-tag`) de `DetectionPanel.tsx`. `?estado=` y `?ataque=` solo existen en el mock.

### B. Resto de pantallas (una función ↔ un dato)
Cada función de `src/api/client.ts` y `src/services/management.ts` trae un comentario `BACKEND_GISS` con el dato que debe devolver. Tabla resumen:
| Función | Pantalla | Debe devolver |
|---|---|---|
| `login`, `register` | Login / Registro | `{token,user}` / `user` |
| `getDashboard` | Dashboard | totales de servidores, eventos e incidentes |
| `getEvents`, `getEventStats("1s"\|"60s")` | Dashboard, Eventos | lista de `Evento`; `EventStats` por ventana |
| `getIncidents`, `updateIncidentStatus` | Incidentes | lista de `Incidente` (con `mitre[]`, `responseAction`); cambia estado |
| `getServers` | Servidores | lista de `ServerItem` |
| `getNotifications` | Notificaciones | lista de `NotificationItem` |
| `simulateEvent` | Botón "Simular" | el `Incidente` creado |
| `getDevices/Sessions/Actions/Protections/LabScenarios`, `runLabScenario` | Dispositivos, Sesiones, Acciones, Protecciones, Laboratorio | listas tipadas en `src/types/index.ts` |
Tipos de salida: `src/types/index.ts` y `src/types/evidence.ts`. Mapeo campo por campo: `MAPEO_BACKEND_FRONTEND.md`.

### C. Quitar la marca "simulado"
En `src/hooks/useCyberShieldData.ts` cambia `const MOCK_MODE = true` a `false` (o bórralo). Así `demo` solo se activa si el backend no responde. En `services/management.ts` devuelve `source:"api"` para que desaparezca el aviso "DATOS SIMULADOS" de esas pantallas.

### D. Verificar
1. `grep -rn BACKEND_GISS src` → recorre la lista; cada punto debe quedar conectado o descartado.
2. DevTools → Network: una lectura de evidencia por incidente; sin 4xx/5xx; sin peticiones tras `CONTAINED`.
3. Un incidente real por estado (`DETECTED`, `RESPONDING`, `CONTAINED`, `FAILED`, `ESCALATED`) y F5 en cada uno: la misma pantalla.
4. Consola sin errores; ningún comando de un ataque aparece en otro.

## 7. Reglas del contrato que la pantalla asume (para que no "mienta")
- `timestamp` ISO 8601 UTC; sin timestamp válido el círculo queda gris.
- `stage` ∈ `ATTACK_RECEIVED, DETECTED, RULE_APPLIED, INCIDENT_CREATED, RESPONDING, CONTAINED, FAILED, ESCALATED`.
- Círculo 5 "Acción ejecutada": entrada `RESPONDING` con `success:true`. Círculo 6 verde y "Empresa protegida": solo con entrada `CONTAINED` **y** `verification_result:"contained"`. En `FAILED/ESCALATED` es rojo/ámbar, nunca verde.
- `response.failure_reason` ya sanitizado (sin rutas ni credenciales). `response.notification.notified:true` solo si el ingeniero fue avisado de verdad.
- El payload de ejemplo `07_evidence_payload_example.json` **no venía en el material** que recibí: el contrato salió del Plan Maestro y del mock. Compáralo con el real.

## 8. Rollback
El paquete anterior (`D3_Jacobo_CyberShield.zip`) conserva la capa de datos con axios. `CAMBIOS_D4.diff` (diff contra D3) permite revertir: `patch -R -p1 < CAMBIOS_D4.diff`.
