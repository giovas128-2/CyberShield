# CyberShield Frontend

Frontend del MVP de CyberShield desarrollado con React + TypeScript + Vite.

## Ejecutar

```bash
npm install
npm run dev
```

La API de FastAPI debe ejecutarse por defecto en `http://localhost:8000`.
Puedes cambiarla creando `.env` a partir de `.env.example`.

## Endpoints usados

- `POST /auth/register`
- `POST /auth/login`
- `GET /dashboard/summary`
- `GET /events`
- `GET /incidents`
- `POST /events/simulate`

## Estructura

- `src/pages`: Login, registro y vistas principales.
- `src/layout`: consola/navegación principal.
- `src/components`: componentes reutilizables.
- `src/api`: cliente y normalización de respuestas del backend.
- `src/data`: datos demo para cuando la API no está disponible.
- `src/types`: tipos TypeScript.
- `src/utils`: formato y utilidades.
- `src/styles`: estilos globales.
