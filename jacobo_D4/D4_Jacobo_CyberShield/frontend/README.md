# CyberShield Frontend (desacoplado · D4)

React 18 + TypeScript + Vite. **No se conecta al backend**: no usa fetch, axios ni endpoints. Todos los datos salen de un único mock: `src/mocks/mockData.ts`.

## Ejecutar solo el frontend
```bash
npm install
npm run dev      # http://localhost:5173  (login: cualquier correo válido + contraseña; el mock acepta todo)
npm run build    # tsc --noEmit && vite build  -> carpeta dist/
npm run preview  # sirve dist/ para probar el build
```

## Rutas para la demo
`#/login/cybershield` · `#/dashboard` · `#/events` · `#/incidents` · `#/incidents/INC-077/evidence` · `#/notifications` · `#/actions` · `#/empresa-demo/login`
Evidencia: `?ataque=brute_force|ransomware&estado=detected|responding|contained|failed|escalated` (solo mock).

## Para quien integra
Lee `../README_INTEGRACION_GISS.md` y `../MAPEO_BACKEND_FRONTEND.md`. Puntos de conexión: `grep -rn BACKEND_GISS src`.
Documentos de días anteriores (César/Alex/Ola) están en `docs_anteriores/` solo como historial; pueden mencionar endpoints que ya no existen aquí.
