# CyberShield — Análisis contextual de proyectos (fase inicial)

## Objetivo
Relacionar una revisión estática de un ZIP, archivos sueltos o un repositorio
público de GitHub con un contexto declarado por el usuario para **proponer
controles defensivos revisables**, sin ejecutar el código ni instalar reglas.

## Ruta y experiencia de usuario
Ruta existente: `/#/code-review`. El menú y encabezado muestran
**Análisis de proyectos**, conservando las funciones previas de auditoría.

1. Elegir **Proyecto ZIP** (predeterminado), **Repositorio GitHub público**
   o **Archivos locales**. El ZIP tiene límite de 8 MB comprimidos y el
   analizador evita extracción en disco o ejecución.
2. Ingresar nombre opcional, descripción libre (hasta 1500 caracteres),
   tipo de aplicación (web, API, móvil, escritorio, script, etc.) y
   características conocidas: internet, inicio de sesión, datos sensibles.
3. Pulsar **Analizar seguridad**. La aplicación usa el analizador existente.
4. El backend añade `project_advice` a la respuesta del mismo endpoint
   de revisión. La pantalla muestra descripción declarada, lenguajes
   identificados **solo por extensiones**, hallazgos y protecciones
   sugeridas con prioridad, razón, evidencia y plan de validación.

## Atribución y limitaciones
- `origin=code_pattern`: la regla identificó un posible patrón inseguro;
  se muestran archivo, línea y regla. **No es vulnerabilidad confirmada**.
- `origin=user_declared`: recomendación preventiva derivada de un campo
  que marcó la persona. **No es evidencia obtenida del código**.
- El texto libre de la descripción se reproduce como descripción del usuario;
  no se transforma en hechos validados. Las características marcadas y el
  tipo de aplicación son los datos de perfil utilizados por el motor inicial.
- El motor trabaja con seis categorías de reglas estáticas existentes,
  más contextos declarados. No acredita análisis exhaustivo, pruebas
  de penetración, presencia de versiones vulnerables ni protección desplegada.
- No se registran nuevas protecciones, incidentes o cambios en PostgreSQL.
- El modelo local Ollama se usa actualmente en el catálogo MITRE.
  **Esta fase contextual aún es determinista**, no una auditoría libre con IA.
  Será posible añadir posteriormente una interpretación Ollama bajo
  autorización, con restricciones para no enviar código o secretos.
- La casilla existente de "IA externa opcional" conserva su comportamiento
  anterior: permanece desactivada por defecto. Si se activa en ZIP, puede
  enviar fragmentos al proveedor externo configurado, no a Ollama.
  No habilitarla para proyectos con credenciales o información sensible.
- El usuario no debe adjuntar secretos, archivos `.env` reales, tokens
  o bases con datos personales.
- El revisor debe tener rol de administrador o ingeniero.

## Archivos de la implementación
- `backend/app/services/intelligence/project_advisor.py`: motor con
  clasificación transparente de recomendaciones.
- `backend/app/api/intelligence.py`: parámetro opcional `context`
  en POST `/code-review/files`, `/code-review/github` y `/code-review/zip`.
  Las llamadas antiguas sin `context` siguen siendo válidas.
- `frontend/src/pages/CodeSecurityReviewPage.tsx`: captura de perfil
  y envío del contexto a los endpoints existentes.
- `frontend/src/components/ProjectRecommendationReport.tsx`:
  presentación de propuestas y referencias CWE.
- `frontend/src/styles/project-recommendations.css`.
- `backend/tests/test_project_advisor.py`: pruebas unitarias.

## Verificación en el worktree de pruebas
```bash
cd /mnt/c/Users/Giovas128/downloads/CyberShield-ThreatCatalog
git pull --ff-only

PYTHONPATH=backend /mnt/c/Users/Giovas128/downloads/CyberSHield/backend/venv-wsl/bin/python \
  -m unittest discover -s backend/tests -p 'test_project_advisor.py' -v

cd frontend
npm run build
```

Para probar en navegador, reiniciar **solo el uvicorn del puerto 8001**
después de comprobar su PID y directorio de trabajo. Mantener
`CYBERSHIELD_LOCAL_AI_ENABLED=1` y
`CYBERSHIELD_LOCAL_AI_MODEL=qwen3:1.7b` si se desea conservar la IA
MITRE, aunque el diagnóstico contextual no la utiliza.
No detener `cybershield-api.service` ni el puerto 8000.

En `http://localhost:8001/#/code-review`, usar un proyecto ZIP pequeño
sin secretos, añadir tipo `API`, marcar inicio de sesión si corresponde,
ejecutar y revisar el bloque **Diagnóstico contextual del proyecto**.

## Siguientes mejoras
- Interpretación con Ollama local de hallazgos y contexto **tras solicitarla
  explícitamente**, sin enviar archivos completos al modelo.
- Comparar los controles sugeridos con medidas ya configuradas y con
  telemetría verificable del servidor, evitando afirmar que están instalados.
- Motor de dependencias y versiones con fuentes oficiales comprobables;
  actualmente el escáner no determina CVE aplicables por solo observar
  un lenguaje de programación.



## Fase posterior — Interpretación del diagnóstico con Ollama local (opcional)

La página **Análisis de proyectos** mantiene el diagnóstico por reglas y
añade un panel **Interpretar diagnóstico con IA local** dentro del informe.
No se sustituye ni modifica el escáner previo: la IA recibe un resumen
suministrado por el navegador, no vuelve a auditar el ZIP.

- Servicio: `backend/app/services/intelligence/local_project_ai.py`.
- Endpoint: `POST /intelligence/local-ai/projects/interpret`, JWT +
  rol `engineer` o `admin`, solo tras pulsar el botón.
- Vista: `frontend/src/components/ProjectLocalAIInterpretation.tsx`.
- Ollama utiliza el mismo conector existente y puerto loopback fijo
  `127.0.0.1:11434`; modelos permitidos `qwen3:0.6b`,
  `qwen3:1.7b`, `qwen3:4b`.
- Permanece apagado si `CYBERSHIELD_LOCAL_AI_ENABLED` no es `1`.
- No se envían ZIP, código, archivos, rutas, líneas ni muestras al
  modelo. Solo tipo, descripción acotada del usuario (máximo 600
  caracteres), características declaradas, lenguajes por extensión
  y códigos de recomendaciones admitidos por el motor.
- La descripción se trata como **dato no confiable**. Se redactan
  patrones comunes de tokens, correos, URLs e IPs; esta redacción
  es parcial, no garantiza anonimización. No introducir secretos.
- El servicio reconstruye razones y medidas de un catálogo permitido;
  no acepta texto arbitrario del cliente como instrucciones de defensa.
- La respuesta se marca como `ollama_local_project` con
  `automatic_application=false` y `human_review_required=true`.
  No modifica PostgreSQL, incidentes ni controles. La narración puede
  equivocarse y requiere contraste con la evidencia del escáner.
- El bloque de **IA externa opcional** sigue siendo una función separada
  y no utiliza Ollama; mantenerlo apagado para no enviar fragmentos a
  proveedores externos.

### Pruebas locales sin inferencia real

```bash
cd /mnt/c/Users/Giovas128/downloads/CyberShield-ThreatCatalog
git pull --ff-only

PYTHONPATH=backend /mnt/c/Users/Giovas128/downloads/CyberSHield/backend/venv-wsl/bin/python \
  -m unittest discover -s backend/tests -p 'test_local_project_ai.py' -v

cd frontend
npm run build
```

La prueba end-to-end necesita reiniciar **solo el Uvicorn de pruebas**
en puerto 8001 para registrar la nueva ruta, sin tocar el servidor
principal 8000 ni reinstalar Ollama. Confirmar antes que la ruta
`/intelligence/local-ai/projects/interpret` esté en
`http://127.0.0.1:8001/openapi.json`. Luego volver a analizar el ZIP
y pulsar **Interpretar con IA local** bajo el diagnóstico.


## Fase de comparación — Recomendaciones contra ocho controles históricos

El informe contextual ahora incorpora una comparación orientativa al final:
**Comparación con las ocho protecciones de CyberShield**.

- Endpoint autenticado: `POST /intelligence/projects/compare-protections`
  para usuarios `admin` o `engineer`.
- Entrada: solo lista validada de IDs de recomendaciones, sin ZIP, texto libre,
  evidencia de archivos, claves ni datos de servidores.
- Consulta el catálogo real con `list_protections(db)` y utiliza únicamente
  los controles históricos `c1` a `c8`; no presume que las propuestas
  pendientes ya sean instalables.
- Motor: `project_protection_comparison.py`. Relaciones conservadoras:
  inicio de sesión ↔ c1 (monitoreo de fuerza bruta);
  información sensible ↔ c5 (telemetría de conexiones externas)
  y c6 (escenario **simulado** de posible exfiltración).
  Son **controles complementarios**, no correcciones directas.
- Las coincidencias de consultas SQL, TLS, depuración, contraseñas incrustadas
  y otras medidas que requieren cambios de aplicación NO se presentan como
  resueltas por las protecciones históricas.
- Cada ficha muestra límites de aplicabilidad y la advertencia
  `verified_for_project=false`. Incluso si c1 figura como integrado y
  ejecutado/verificado en el catálogo, NO acredita protección para el ZIP.
- No se ejecutan controles, no se crean propuestas y no se escriben tablas.
- Esta etapa no necesita Ollama: ofrece una comparación verificable del
  catálogo y evita depender de textos generados para afirmar cobertura.

Prueba:

```bash
cd /mnt/c/Users/Giovas128/downloads/CyberShield-ThreatCatalog
git pull --ff-only
PYTHONPATH=backend /mnt/c/Users/Giovas128/downloads/CyberSHield/backend/venv-wsl/bin/python \
  -m unittest discover -s backend/tests -p 'test_project_protection_comparison.py' -v
cd frontend && npm run build
```

Para probar desde `http://localhost:8001/#/code-review`:
- Reiniciar únicamente el uvicorn de pruebas después de verificar su PID
  y directorio de trabajo.
- Volver a analizar el ZIP para que aparezca el bloque de comparación.
- No modificar el servicio `cybershield-api.service` del puerto 8000.
