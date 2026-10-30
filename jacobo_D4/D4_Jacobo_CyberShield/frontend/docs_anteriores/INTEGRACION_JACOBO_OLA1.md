# Integración César + Jacobo — CyberShield Frontend

Base utilizada: `frontend(4).zip` de César.  
Entrega integrada: OLA 1 de Jacobo (`files (3).zip`).

## Se conservó de César
- Login y registro actuales.
- Cliente Axios y `VITE_API_URL`.
- Compatibilidad con `mvp-session` sin enviar un Bearer falso.
- `GET /dashboard/summary`, `GET /events`, `GET /incidents`, `GET /servers`.
- `GET /events/stats`, `GET /notifications` si existen.
- `POST /events/simulate` con el body ya adaptado al backend.
- `PATCH /incidents/{id}/status`.
- Dashboard actual con eventos/s, eventos/min, scope y notificaciones.
- Vista de incidentes con guía de investigación y resolución.
- Vista real de servidores.
- Polling de 5 segundos y manejo demo/stale.
- Estilos visuales existentes.
- Se mantienen Seguridad y Configuración como pantallas reservadas.

## Se integró de Jacobo
- Navegación por rutas reales con `AppLayout`.
- `/events` como página independiente con filtros.
- `/incidents/:id` para detalle navegable.
- `/devices`, `/sessions`, `/actions`, `/protections`, `/lab`.
- MITRE ATT&CK en incidentes, protecciones y laboratorio.
- Mocks controlados para módulos cuyos endpoints aún no existen.
- `useResource` para loading/error/empty y fallback de demo.
- Servicios/normalizadores provisionales de gestión.
- Indicadores INTEGRADA / SIMULACIÓN CONTROLADA.

## Importante
Los endpoints de dispositivos, sesiones, acciones, protecciones y laboratorio están en `src/api/endpoints.ts` y permanecen en `null` hasta que César confirme el contrato del backend. Mientras tanto las pantallas muestran datos simulados de forma explícita; no se inventan rutas.

## Validación realizada
- `tsc --noEmit`: OK.
- El build Vite completo no se ejecutó en este contenedor porque los `node_modules` originales del ZIP provienen de Windows y Rollup requiere el binario nativo de Linux. En Windows usar los `node_modules` originales o ejecutar `npm install` y luego `npm run build`.

## Cómo usar
1. Haz respaldo de tu carpeta `frontend` actual.
2. Conserva tu `.env` actual. El ZIP integrado no incluye `.env` ni `node_modules`.
3. Extrae esta carpeta como tu nuevo frontend.
4. Copia tu `.env` al directorio raíz del frontend. Debe conservar, por ejemplo:
   `VITE_API_URL=http://localhost:8000`
5. Ejecuta `npm install` si no tienes dependencias locales.
6. Ejecuta `npm run build` y después `npm run dev`.
7. Prueba primero Dashboard, Incidentes, Servidores, simulación HIGH y cambio de estado para confirmar que lo que ya funcionaba sigue funcionando.
8. Después revisa Dispositivos, Sesiones, Acciones, Protecciones y Laboratorio.
