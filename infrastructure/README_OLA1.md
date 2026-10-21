# CyberShield - OLA 1

## Objetivo
Preparar telemetría real y repetible de un servidor de laboratorio.

## Servidor
- Hostname: srv-cyber-01
- Rol: Wazuh Manager / backend
- Tailscale: 100.77.51.7

## Agente
- Hostname: srv-yahir-01
- IP Tailscale: 100.125.119.56
- Wazuh Agent: activo
- Heartbeat: cada ~30 segundos hacia `/servers/heartbeat`

## Telemetría validada
1. Autenticación SSH exitosa.
2. Autenticación SSH fallida.
3. Uso autorizado de sudo.
4. Modificación de `/company-demo/config/demo.conf`.
5. Heartbeat periódico.
6. Wazuh File Integrity Monitoring.

## Criterio
La infraestructura genera eventos reales desde un servidor de laboratorio autorizado y los entrega al Wazuh Manager/backend.
