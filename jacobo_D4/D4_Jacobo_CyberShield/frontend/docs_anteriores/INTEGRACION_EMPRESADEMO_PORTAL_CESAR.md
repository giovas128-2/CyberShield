# Integración EmpresaDemo dentro del frontend maestro

## Objetivo
Integrar la entrega de EmpresaDemo de Jacobo sin reemplazar la estructura existente de CyberShield.

## Flujo de acceso implementado
1. `#/login` muestra un selector con dos opciones: **CyberShield** y **EmpresaDemo**.
2. **CyberShield** abre `#/login/cybershield` y conserva la autenticación real existente.
3. **EmpresaDemo** abre `#/empresa-demo/login`, usando únicamente datos ficticios y sesión de demostración.
4. Al cerrar sesión en CyberShield, el guard redirige a `#/login`.
5. Al usar **Salir de la demo**, EmpresaDemo limpia su estado de sesión y vuelve a `#/login`.

## Archivos agregados
- `src/pages/PortalChoicePage.tsx`
- `src/empresademo/EmpresaDemoLayout.tsx`
- `src/empresademo/empresademo.css`
- `src/empresademo/fixtures.ts`
- `src/pages/empresademo/*.tsx`

## Archivos modificados
- `src/App.tsx`: rutas nuevas y selector de portales.
- `src/pages/Login.tsx`: botón para volver al selector.
- `src/styles/styles.css`: estilos aislados del selector.
- `src/empresademo/EmpresaDemoLayout.tsx`: salir vuelve al selector central.
- `src/pages/empresademo/EDLogin.tsx`: botón para cambiar tipo de acceso.

## No modificado
No se sustituyeron páginas de CyberShield, API client, hooks, servicios, reglas MITRE, páginas de incidentes ni lógica del backend.
