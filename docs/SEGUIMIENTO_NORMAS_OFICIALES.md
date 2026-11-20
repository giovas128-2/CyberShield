# CyberShield · Investigación de normas y fuentes oficiales

## Qué hace
En Protecciones defensivas se muestran las 8 protecciones históricas (C1-C8)
junto con sus técnicas MITRE y una alineación **orientativa** a funciones NIST
CSF y CIS Controls (no equivale a certificación ni mapeo oficial ratificado).

El monitor realiza consultas HTTPS a destinos fijos y públicos:
1. MITRE ATT&CK: https://attack.mitre.org/resources/versions/
2. NIST CSF: https://www.nist.gov/cyberframework
3. CIS Controls: https://www.cisecurity.org/controls
4. CISA KEV: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json

La primera consulta correcta establece una **referencia observada** en PostgreSQL.
Si una comprobación posterior encuentra una versión distinta o un cambio del
contenido identificado del catálogo KEV, la fuente aparece como
**Cambio por revisar**. No significa que una técnica concreta ni uno de los
servidores estén comprometidos. Si la fuente falla, la pantalla muestra
**No disponible**, manteniendo la última comprobación válida separada.

**Limitaciones**: MITRE, NIST y CIS se comparan por su versión pública visible;
una noticia, nueva guía, corrección editorial o cambio dentro de una misma
versión podría no detectarse. CISA KEV no constituye el catálogo completo de
vulnerabilidades ni garantiza que una CVE afecte al laboratorio. Los mapeos
NIST/CIS son sugerencias documentales, no controles certificados.

## Privacidad y seguridad
- El monitor no envía IP, inventario de servidores, incidentes, secretos,
  telemetría ni código fuente a MITRE, NIST, CIS o CISA.
- Las fuentes consultadas pueden registrar la dirección IP pública del
  servidor desde el que se hace la petición HTTPS.
- No envía contenido a un LLM. Se usa consulta y comparación verificable;
  ninguna salida de IA se considera autoridad normativa.
- URLs allowlist fijas, HTTPS, sin redirecciones, con límites de descarga.
- No descarga ni ejecuta scripts de terceros ni modifica los 8 controles.
- No ejecuta respuesta defensiva, actualización de reglas, bloqueo, ni aplica
  una nueva recomendación sin evaluación y pruebas humanas.
- Si la fuente no responde, no se presentan datos inventados ni se indica
  que CyberShield esté actualizado.

## Instalación
Desde WSL en la raíz del repositorio CyberShield, actualiza rama y valida
las pruebas antes de migrar:

    git fetch origin
    git merge --ff-only origin/feature/intelligence-protection-coverage
    PYTHONPATH=backend:. backend/venv-wsl/bin/python -m unittest discover \
      -s backend/tests -p 'test_official_frameworks.py' -v
    cd frontend && npm run build && cd ..

Aplicar **solo una vez** la migración aditiva:

    backend/migrations/013_official_framework_checks.sql

Esta migración crea exclusivamente
public.intelligence_official_framework_checks. Verifica el SQL y usa la
conexión PostgreSQL autorizada del laboratorio (psql o herramienta DB).
No modifiques las migraciones históricas 005-012 ni vuelvas a ejecutarlas.

Después reinicia **solo** el servicio FastAPI:

    sudo systemctl restart cybershield-api.service

En la interfaz: Protecciones defensivas → Vigilancia de normas, marcos y
amenazas → Consultar fuentes oficiales. Se requiere sesión **admin/engineer**
para la comprobación manual. La lectura de resultados utiliza autenticación.

## Revisión diaria opcional existente
Si ya está habilitado cybershield-intelligence-sync.timer, su ejecución
diaria a las 03:30 hora local añade este monitor a los catálogos CISA/MITRE
existentes tras aplicar la migración 013; no hay que crear otro temporizador.

Consultar el estado:

    systemctl list-timers --all | grep cybershield-intelligence
    systemctl status cybershield-intelligence-sync.timer

Si no está habilitado, la pantalla sigue permitiendo el chequeo manual.
La revisión diaria es documental; no aplica automáticamente recomendaciones.

## Qué revisar ante una actualización
1. Abrir el enlace oficial y comprobar la fecha, versión y alcance.
2. Identificar si la técnica, vulnerabilidad, dispositivo o salvaguarda
   corresponde al entorno realmente desplegado.
3. Analizar impactos, falsos positivos y compatibilidad de versiones.
4. Registrar una propuesta en el flujo humano de protección.
5. Probar cualquier regla futura en laboratorio antes de habilitarla.

**Nunca concluir que hubo un ataque o que una norma fue implementada solo
porque una versión oficial ha cambiado.**
