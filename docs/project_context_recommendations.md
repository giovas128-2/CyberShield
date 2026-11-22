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
