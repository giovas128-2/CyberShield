# Fase 1 — Catálogo documental unificado (MITRE + CISA)

Rama: `feature/threat-catalog-foundation`. Esta primera entrega usa solo las
tablas existentes de las migraciones **005** y **006**; **no hay nueva migración**.

## Qué se añade

Endpoint autenticado de solo lectura: `GET /intelligence/threat-catalog`.

Parámetros: `kind=all|mitre|cisa`, `search`, `page`, `size` (1 a 100).
La respuesta ofrece entradas con fuente, versión observada, enlace documental,
fecha, conteo total y etiqueta `official_catalog_imported`.

Los datos provienen de PostgreSQL después de que los importadores **ya
existentes** hayan validado e importado MITRE ATT&CK Enterprise y CISA KEV.
La cifra mostrada depende de los datos realmente importados. No genera 1,000
amenazas imaginarias y no equivale a 1,000 protecciones.

## Qué NO hace

- No instala, activa, prueba ni ejecuta protecciones.
- No consulta fuentes externas al recibir el GET.
- No envía datos internos ni usa API de IA.
- No modifica tablas, no reinicia servicios, no toca los controles c1–c8.
- Todavía no contiene catálogo de recomendaciones empresariales o marketplace.

## Validación en Ubuntu WSL

Antes de cambiar de rama, ejecutar `git status --short` y proteger cambios locales.
Una vez en esta rama, ejecutar desde la raíz:

```bash
backend/venv-wsl/bin/python -m py_compile \
  backend/app/services/intelligence/threat_catalog.py \
  backend/app/api/intelligence.py
PYTHONPATH=backend backend/venv-wsl/bin/python -m unittest \
  discover -s backend/tests -p test_threat_catalog.py -v
```

Tras la revisión y con el servicio de backend reiniciado de forma controlada
(vía `cybershield-api.service`), verificar OpenAPI y consultar la ruta con JWT
desde una sesión autorizada. No compartir JWT en chats o registros.

## Siguientes entregas

1. Pantalla de catálogo con filtros y paginación.
2. Métricas por fuente, versiones verificadas y estado de importación.
3. Validación automática documentada de cambios oficiales y deduplicación.
4. Relación explicable amenaza→mitigación→protección (sin instalar).
5. Propuestas opcionales con IA, únicamente a partir de metadatos públicos
   verificados y con revisión humana.


## Interfaz de Protecciones: panel de amenazas (segunda entrega)

Se ha añadido `frontend/src/components/ThreatCatalogPanel.tsx` y
`frontend/src/styles/threat-catalog.css`. El panel aparece en
`ProtectionsPage.tsx`, después de la vigilancia normativa. Tiene filtros
MITRE/CISA, búsqueda literal y paginación de diez elementos por página.

El panel solicita el endpoint anterior con el JWT de la sesión actual.
No muestra registros ficticios ni interpreta que una técnica MITRE sea
una vulnerabilidad explotada. El estado vacío indica que los catálogos
pueden no estar importados.

Antes de habilitar en el laboratorio real, validar en el worktree:

```bash
cd /mnt/c/Users/Giovas128/downloads/CyberShield-ThreatCatalog
PYTHONPATH=backend /mnt/c/Users/Giovas128/downloads/CyberSHield/backend/venv-wsl/bin/python \
  -m unittest discover -s backend/tests -p 'test_threat_catalog.py' -v
cd frontend
npm ci
npm run build
```

**No reiniciar** `cybershield-api.service` para apuntarlo al worktree de
pruebas; el servicio principal sigue usando su directorio habitual. Antes
de integrar este cambio allí se hará revisión de diff, prueba de conexión
PostgreSQL y despliegue planificado.
