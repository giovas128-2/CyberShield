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

## Navegación: sección independiente Catálogo

La investigación documental ya no se muestra dentro de **Protecciones**.
El menú lateral (**GESTIÓN**) incluye **Catálogo**, que abre la ruta
`/#/catalog` en la interfaz React. La pantalla integra:

- Buscador y filtros para el catálogo MITRE/CISA, paginado y obtenido de PostgreSQL.
- Vigilancia de versiones y fuentes oficiales MITRE, NIST, CIS, CISA.
- Interpretación opcional de metadatos oficiales con IA bajo solicitud explícita,
  si ya está configurada.

**Protecciones** mantiene el catálogo de controles c1–c8 y las propuestas
pendientes, sin cambios en sus capacidades de ejecución.

### Para probar la nueva pantalla sin alterar el sistema principal

Desde el worktree `CyberShield-ThreatCatalog`:

```bash
cd /mnt/c/Users/Giovas128/downloads/CyberShield-ThreatCatalog
git pull --ff-only
cd frontend
npm run build
```

Si ya está corriendo un FastAPI de pruebas en el puerto 8001 con este worktree,
refrescar `http://localhost:8001/#/catalog` (la ruta usa HashRouter).
El backend de pruebas sirve su propio `frontend/dist`. Para usar este puerto
no hace falta editar `vite.config.ts`, cuyo proxy del modo de desarrollo sigue
apuntando a 8000. Mantener el servidor de producción independiente.


## Rediseño visual azul (22 de noviembre de 2026)

- `CatalogPage.tsx`: encabezado azul marino, etiquetas de fuentes, paneles con
  conteos consultados a `GET /intelligence/summary` y aviso explícito de
  consulta documental; sin números simulados.
- `catalog-blue.css`: gradientes azules, tarjetas y filtros más contrastados,
  secciones MITRE/CISA y vigilancia oficial con estilos exclusivos de Catálogo;
  diseño adaptable a pantallas pequeñas.
- `enterprise-light.css`: refuerzo azul de fondo, cabecera y héroes
  operativos únicamente con el tema claro. No cambia rutas ni datos.

**Validación pendiente de ejecutar en WSL:** `git pull --ff-only`,
`cd frontend && npm run build`, luego abrir
`http://localhost:8001/#/catalog` con FastAPI de pruebas levantado
desde el mismo worktree. No modificar el servicio principal del puerto 8000.


## Fase 2A — Mitigaciones documentadas MITRE en las fichas

Se incorpora `MitreMitigations.tsx` en la página Catálogo. Por cada técnica
MITRE, el botón **Ver mitigaciones documentadas** solicita bajo demanda
`GET /intelligence/techniques/{attack_id}`, endpoint autenticado que ya
existía en la aplicación y consulta exclusivamente las relaciones persistidas
por el importador de MITRE.

- Muestra códigos, nombres y descripciones MITRE asociadas a cada técnica.
- Si no existen relaciones, lo indica sin inventar mitigaciones.
- Las CVE de CISA conservan sus fichas documentales; no se les atribuye
  automáticamente una mitigación MITRE sin evidencia adicional.
- La consulta no instala defensas, no cambia las reglas Wazuh, no crea
  incidentes y no requiere migraciones ni credenciales adicionales.
- El paso siguiente será la **interpretación asistida con IA**, solo con
  evidencias oficiales verificadas y revisión humana, sin afirmar que
  una defensa propuesta está desplegada.

Validación requerida en el worktree de pruebas:

```bash
cd /mnt/c/Users/Giovas128/downloads/CyberShield-ThreatCatalog
git pull --ff-only
cd frontend
npm run build
```

Después, en la instancia de pruebas en puerto 8001, abrir
`http://localhost:8001/#/catalog`, filtrar MITRE y consultar una técnica
con mitigaciones conocidas como T1110. Comprobar también un registro sin
relaciones MITRE para verificar que informa correctamente. Mantener separado
el servicio principal en puerto 8000.


## Fase 2B — Informe documental en español (sin costo ni IA generativa)

Se incorpora un informe que reutiliza las técnicas y mitigaciones MITRE
existentes de PostgreSQL. La consulta requiere sesión autenticada y
**solo ejecuta SELECT**, sin nuevas migraciones.

- Backend: `app/services/intelligence/technique_research.py`.
- API: `GET /intelligence/techniques/{attack_id}/research`.
- Interfaz: `TechniqueResearchPanel.tsx`, visible al abrir mitigaciones
  MITRE y pulsar **Preparar informe documental**.
- Contenido: identificación de técnica MITRE, total y nombres de mitigaciones
  realmente vinculadas, referencia oficial y tareas de comprobación humana.
- Estado explícito: `documental_sin_ia_generativa`. No se presenta como
  IA entrenada ni como evaluación real de un servidor.
- UX: primero aparecen tres mitigaciones; se pueden desplegar todas,
  y abrir/cerrar descripciones extensas. Las CVE CISA no se relacionan
  automáticamente con técnicas MITRE.

Pruebas locales de servicio (sin base ni red):

```bash
cd /mnt/c/Users/Giovas128/downloads/CyberShield-ThreatCatalog
git pull --ff-only
PYTHONPATH=backend /mnt/c/Users/Giovas128/downloads/CyberSHield/backend/venv-wsl/bin/python \
  -m unittest discover -s backend/tests -p 'test_technique_research.py' -v
cd frontend && npm run build
```

Luego, confirmar en el backend **de pruebas** del puerto 8001 que el
nuevo GET está disponible; si uvicorn está sin `--reload`, reiniciar
**solo ese proceso**, nunca `cybershield-api.service` de producción.
Probar la pantalla `/#/catalog` con `T1003` o `T1110`.

La integración de IA generativa genuina queda para un paso aparte, con
revisión de costos, autorización explícita, controles de datos públicos,
limitaciones y validación humana. La IA opcional existente para versiones
oficiales no cambia y no se activa por este informe.


## Fase 2C — Integración preparada para IA local Ollama (no activada)

El modelo local queda **DESACTIVADO POR DEFECTO**. No se ha descargado
ni instalado Ollama, no se han abierto puertos y no se ha activado el endpoint
de generación. No usar el backend principal antes de completar pruebas.

### Código nuevo

- `backend/app/services/intelligence/local_ollama.py`: conexión únicamente
  a `http://127.0.0.1:11434`, sin proxies externos, sin escritura en BD.
- `GET /intelligence/local-ai/status`: estado Ollama, modelo y disponibilidad.
- `POST /intelligence/local-ai/techniques/{attack_id}/interpret`: genera
  interpretación en español SOLO tras clic del ingeniero.
- Endpoints protegidos por autenticación y rol `admin` o `engineer`.
- `LocalAIInterpretation.tsx`: control opcional dentro de una técnica MITRE.
  Si está desactivada, muestra un aviso sin enviar solicitudes de generación.
- `backend/tests/test_local_ollama.py`: comprueba desactivación,
  modelos permitidos y aislamiento de red.

### Seguridad y privacidad

1. El único destino de solicitudes del backend es el servicio local de Ollama.
2. Solo se admiten los modelos `qwen3:0.6b`, `qwen3:1.7b` y `qwen3:4b`,
   instalados localmente. No se admiten modelos `:cloud`.
3. Únicamente se envían datos públicos MITRE ya importados, con límites
   de longitud. NO se envían IPs de servidores, incidentes o credenciales.
4. No hay llamadas automáticas de generación. `stream=false`;
   `keep_alive=0` para descargar el modelo al terminar de responder.
5. La respuesta se marca como texto generado por IA que puede equivocarse.
   Requiere revisión humana; nunca ejecuta protecciones ni cambia tablas.
6. Una IA pequeña no garantiza precisión ni traducción exacta; contrastar
   siempre con la documentación oficial.

### Revisión previa de hardware en WSL (solo lectura)

```bash
echo "=== RAM EN WSL ==="
free -h
echo "=== CPU ==="
nproc
echo "=== ESPACIO DISPONIBLE ==="
df -h ~ | tail -n 1
echo "=== GPU NVIDIA (si existe) ==="
command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || echo "No se detectó nvidia-smi"
echo "=== OLLAMA INSTALADO ==="
command -v ollama || echo "Ollama todavía no está instalado en WSL"
```

**No instalar ni descargar** hasta valorar RAM/CPU/espacio. Ollama usa
recursos que pueden afectar Wazuh/PostgreSQL. Tampoco activar modelos con
nombres `:cloud` si se desea mantener todo local y sin costo por uso.

### Habilitación futura (solo cuando el usuario autorice)

En el entorno del proceso **de pruebas**, y solo tras instalar Ollama
y descargar un modelo local compatible:

```bash
export CYBERSHIELD_LOCAL_AI_ENABLED=1
export CYBERSHIELD_LOCAL_AI_MODEL=qwen3:0.6b
```

Estas variables **no tienen efecto sobre un proceso ya iniciado**.
Para aplicarlas, iniciar nuevamente SOLO FastAPI de pruebas en puerto 8001
con su misma configuración de base de datos, sin tocar
`cybershield-api.service` del puerto 8000.

### Pruebas de código local

```bash
cd /mnt/c/Users/Giovas128/downloads/CyberShield-ThreatCatalog
git pull --ff-only
PYTHONPATH=backend /mnt/c/Users/Giovas128/downloads/CyberSHield/backend/venv-wsl/bin/python \
  -m unittest discover -s backend/tests -p 'test_local_ollama.py' -v
cd frontend
npm run build
```

El conjunto anterior solo prueba llamadas simuladas. La generación real con
Ollama queda pendiente de la evaluación del equipo y una prueba aislada.


## Fase 2D — Acciones CISA KEV a partir del importador existente

El archivo `backend/app/services/intelligence/import_cisa_kev.py`
ya conserva el valor `requiredAction` del catálogo CISA KEV dentro
de `intelligence_threats.description`, concatenado mediante el marcador
`\n\nAcción recomendada por CISA: `.

La respuesta de `GET /intelligence/threat-catalog` separa este texto,
únicamente para las fichas de tipo CISA:
- `description`: descripción corta sin duplicar el campo de acción;
- `cisa_required_action`: texto exacto importado, sin modificaciones de IA;
- `cisa_action_origin`: procedencia documental cuando la acción existe.

La interfaz incorpora `CisaRemediationPanel.tsx` con el botón
**Ver acción recomendada por CISA**, fuente oficial y advertencia
de verificación del producto y versión afectada. Si el registro histórico
no contiene el marcador, no inventa ninguna acción.

No hay nuevas tablas, migraciones, escritura SQL, solicitudes a sitios externos,
ejecución de defensas ni inferencias IA para esta vista.
Al cambiar el filtro MITRE/CISA se limpia la búsqueda previa para
no mezclar identificadores Txxxx con CVE-xxxx.

### Pruebas en el worktree aislado

```bash
cd /mnt/c/Users/Giovas128/downloads/CyberShield-ThreatCatalog
git pull --ff-only
PYTHONPATH=backend /mnt/c/Users/Giovas128/downloads/CyberSHield/backend/venv-wsl/bin/python \
  -m unittest discover -s backend/tests -p 'test_cisa_required_action.py' -v
cd frontend && npm run build
```

El backend de pruebas que ya está ejecutándose en puerto 8001
requiere reinicio **solo de ese proceso** para cargar la separación del
campo CISA. Antes de reiniciar, comprobar su PID/directorio de trabajo
para no tocar el proceso principal del puerto 8000. La RAM y el servicio
de Ollama permanecen independientes.
