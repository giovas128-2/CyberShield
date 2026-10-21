# OLA 1 - Telemetría y campos útiles para MITRE

## Eventos observados

| Evento | Campos útiles |
|---|---|
| SSH fallido | timestamp, usuario, proceso sshd, IP origen, resultado |
| sudo autorizado | timestamp, usuario, comando ejecutado, usuario destino |
| Cambio de archivo | timestamp, ruta, evento de modificación |
| Heartbeat | servidor, IP, agente, estado, last_seen |

## Ejemplo SSH
- Usuario: yahir
- Resultado: authentication failure / Failed password
- Proceso: sshd
- Origen: 127.0.0.1
- Timestamp: registrado en auth.log/journal

## Ejemplo sudo
- Usuario: yahir
- Usuario destino: root
- Comando: sudo/tee/grep/etc.
- Timestamp: registrado por Wazuh

## Ejemplo FIM
- Archivo: /company-demo/config/demo.conf
- Evento: File modified
- Fuente: Wazuh syscheck

Los Technique IDs deben ser determinados por el analista a partir del contexto completo del evento; esta entrega no inventa IDs.
