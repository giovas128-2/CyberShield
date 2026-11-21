# CyberShield 2.0: integración de servidores remotos (Windows y Linux)

## 1. Qué es una integración real

La interfaz **Servidores → Añadir servidor** permite que un ingeniero con rol `admin` o `engineer` registre un host autorizado mediante `POST /servers/onboard`.

El backend crea **en una transacción**:
- Un registro en `public.servers`, inicialmente con estado `registered`.
- Un `agent_id` UUID y un **token secreto aleatorio individual** cuya huella SHA-256 se guarda en `server_agent_credentials`. El token en texto claro solo se devuelve en la respuesta inicial.

El servidor remoto corre `heartbeat/cybershield-agent-heartbeat.py --watch`, que envía por HTTPS un heartbeat cada 30 segundos con `Authorization: Bearer <token>` a:

`POST /api/v1/agents/{agent_id}/heartbeat`

El backend valida el token comparando su huella en tiempo constante y rechaza credenciales revocadas. Después de recibir un heartbeat, guarda `last_seen`. El estado **conectado** se calcula solo si el último heartbeat autenticado tiene menos de 90 segundos.

**No se requiere Ubuntu Server ni Tailscale.** Se requiere acceso HTTP(S) **saliente** desde el servidor integrado hasta la API de CyberShield y Python 3 con `httpx`. Para servidores distintos al propio host de CyberShield se debe usar **HTTPS con certificado TLS válido**.

### Aclaración esencial

Un heartbeat confirma recepción de una señal de quien posee el token; **no es autenticación de hardware, inventario de vulnerabilidades, monitoreo de CPU, detección de ataques, ni prueba de seguridad de un host**. Para eventos reales de seguridad incorpora Wazuh/Suricata u otro sensor autorizado y enlaza los eventos al ID registrado del servidor.

## 2. Requisitos de base de datos

Comprueba que las tablas originales y las migraciones están aplicadas:

```sql
SELECT to_regclass('public.servers');
SELECT to_regclass('public.server_agent_credentials');
```

La segunda debe existir. Si no existe, respalda PostgreSQL y revisa `backend/migrations/003_server_agent_credentials.sql` antes de ejecutarla. Asegúrate también de tener la unicidad de IP indicada por `backend/migrations/004_servers_unique_ip.sql`.

No ejecutes migraciones sin verificar el esquema, respaldos y permisos del entorno.

## 3. Exponer la API sin depender de Tailscale

El servicio `cybershield-api.service` original escucha `127.0.0.1:8000`; un servidor remoto **no puede contactar localhost de tu equipo**. Para acceder desde otra máquina:

1. Asigna a CyberShield un nombre DNS o IP alcanzable desde la red de ese servidor, con autorización del administrador.
2. Configura un **proxy inverso HTTPS** (por ejemplo, Nginx/Caddy/Apache con un certificado válido) frente a `http://127.0.0.1:8000`. No publiques PostgreSQL ni el puerto interno de Uvicorn directamente.
3. Restringe acceso mediante firewall y políticas de red. Mantén autenticación, registros de acceso y actualización de certificados.
4. Desde el equipo remoto verifica la URL HTTPS antes de entregar la credencial individual.

Cuando uses redes privadas, evita depender de puertos públicos si el proxy se puede publicar en la LAN. Si usas Internet, planifica filtrado de direcciones y controles adicionales.

## 4. Alta desde CyberShield

1. Inicia sesión como `admin` o `engineer`.
2. Abre **Servidores → Añadir servidor**.
3. Introduce nombre, IP única y sistema operativo del servidor al que **tienes autorización para instalar el agente**.
4. Pulsa **Registrar y crear agente**. Esto **no** hace ninguna conexión remota ni lo marca en línea.
5. Copia el `agent_id` y el token secreto **una sola vez**. Si se pierde, un administrador debe revocar la credencial y registrar un agente nuevo; el token no se puede recuperar de PostgreSQL.
6. En el equipo remoto usa el script del repositorio, envía un heartbeat y observa cómo CyberShield cambia de `Registrado` a `En línea`.

Para un servidor antiguo sin agente individual, selecciona su ficha y utiliza **Vincular el servidor seleccionado**. El endpoint de credencial ya existente es `POST /api/v1/agents/register`.

## 5. Agente real en Linux (bash)

Coloca en el host remoto el archivo `heartbeat/cybershield-agent-heartbeat.py` del repositorio aprobado.

```bash
python3 -m pip install httpx

export CYBERSHIELD_AGENT_API='https://cybershield.tudominio.com'
export CYBERSHIELD_AGENT_ID='UUID_DEL_AGENTE'
read -rsp 'Token individual: ' CYBERSHIELD_AGENT_TOKEN
echo
export CYBERSHIELD_AGENT_TOKEN

python3 cybershield-agent-heartbeat.py --watch
```

El token se lee sin mostrarse en pantalla. **No escribas la credencial directamente en el historial de comandos ni la copies a archivos compartidos**.

Para usarlo permanentemente en un host de producción, conviértelo en un servicio del sistema (systemd/supervisor) y utiliza un mecanismo de secretos con permisos mínimos y cuenta sin privilegios. Esta guía muestra el modo interactivo de demostración, no un despliegue administrado completo.

## 6. Agente real en Windows Server (PowerShell)

Coloca el mismo script Python en la máquina Windows.

```powershell
py -m pip install httpx

$env:CYBERSHIELD_AGENT_API = 'https://cybershield.tudominio.com'
$env:CYBERSHIELD_AGENT_ID = 'UUID_DEL_AGENTE'
$secret = Read-Host 'Token individual' -AsSecureString
$env:CYBERSHIELD_AGENT_TOKEN = [System.Net.NetworkCredential]::new('', $secret).Password

py .\cybershield-agent-heartbeat.py --watch
```

Ejecuta con un usuario sin privilegios. Para operación permanente usa un servicio o una tarea administrada con credenciales almacenadas en un gestor de secretos del sistema, no dentro del script ni en el repositorio.

## 7. Verificación sin cambiar eventos ni defensas

- GET `/servers` autenticado debe mostrar la ficha con `agent_connection.state`.
- Antes del primer heartbeat: `registered` / `awaiting_heartbeat`.
- Con heartbeats recientes: `online` / `connected`.
- Sin señales durante más de 90 segundos: `offline` / `disconnected`.
- Tras revocar la credencial mediante el endpoint protegido de agentes: `offline` / `revoked`.
- Cada agente debe tener un UUID y un token únicos.

Si el alta da **503** y menciona la migración 003, no uses el endpoint heredado para intentar fingir conexión: primero revisa la base de datos.

El sistema de eventos, incidentes, respuestas y notificaciones existente **no se modifica** por esta función de conectividad.
