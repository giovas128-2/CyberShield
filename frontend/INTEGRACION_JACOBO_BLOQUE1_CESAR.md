# Integración Jacobo — Bloque 1

Se integró de forma incremental sobre el frontend de César, sin sustituir las páginas, servicios, hooks, mocks ni contratos existentes.

## Archivos agregados
- `src/components/Sidebar.tsx`
- `src/components/OriginChip.tsx`

## Archivos modificados
- `src/layout/AppLayout.tsx`: extrae la navegación al Sidebar reutilizable, agrega drawer responsive y chip de origen; conserva `useCyberShieldData`, `AlertModal`, `Toast`, `Outlet` y navegación de incidentes.
- `src/styles/styles.css`: agrega únicamente estilos del Bloque 1 y dos ajustes de compatibilidad para que el drawer funcione con los estilos previos.

## Estructura conservada
No se modificaron páginas, API, services, hooks, tipos, mocks, MITRE, Incidents, Devices, Sessions, Actions, Protections ni Lab.

## Validación
Ejecutar:
```bash
npx tsc --noEmit
npm run build
```
