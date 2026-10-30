# MAPEO_BACKEND_FRONTEND · Frontend completo + Evidencia de protección / Respuesta real (D1 a D4)

**Punto único de entrada de datos:** `getEvidenceResult(id, estado)` en `src/mocks/evidenceMock.ts` (hoy devuelve el mock) → el JSON real debe pasar por `adaptEvidencePayload(raw)` en `src/components/evidence/adaptEvidence.ts` → los componentes **solo reciben `ev: IncidentEvidence` por props**.
En los archivos de evidencia no hay `fetch` / `axios` / `WebSocket`. Para ver todos los puntos de conexión: `grep -rn BACKEND_GISS src` (un comentario `BACKEND_GISS` en cada archivo que muestra datos dinámicos y uno por campo en `src/mocks/mockData.ts`).

> `07_evidence_payload_example.json` no venía en lo que recibí. El contrato salió del Plan Maestro (Día 1 Sebas/César): `incident_id, event_id, stage, timestamp, source, message, action_type, command_display, result, success`. Los demás campos (`level`, `terminal_lines`, `outcomes`, `tools`, `notification`, `failure_reason`, `reason`, `tool`, `verification_result`, `response_started_at`, `response_finished_at`, `elapsed_time`, `mitre_*`) son **propuesta del frontend**: si el payload real los llama distinto, se corrige solo `adaptEvidence.ts` (+ esta tabla). No se inventó ninguna ruta del backend.

Convención en el código: `BACKEND_GISS: <variable visual> <- <dato backend esperado>`.

## Variables mínimas del Día 2 (dónde se renderiza cada una)
| Variable | Tipo | Ejemplo (mock) | Se muestra en | Fallback si falta |
|---|---|---|---|---|
| `incident_id` | string | `INC-077` (sale de la ruta) | Pantalla 1 · ID de incidente | obligatorio: sin él el adaptador devuelve `null` → "Sin evidencia" |
| `source_ip` | string\|null | `192.168.56.50` | Pantalla 1 · IP de origen | `—` |
| `event_type` | string | `multiple_login_attempts` | P1 · Tipo de evento y P2 · Tipo de incidente actual | valor crudo con `_` → espacios |
| `mitre_id` | string\|null | `T1110` | P1 · MITRE ATT&CK | "Sin clasificación MITRE confirmada" |
| `mitre_name` | string\|null | `Brute Force` | P1 · MITRE ATT&CK | solo se muestra el id |
| `severity` | `NORMAL\|WARNING\|HIGH\|CRITICAL` | `HIGH` | P1 · Severidad | `NORMAL` |
| `status` | `DETECTED\|RESPONDING\|CONTAINED\|FAILED\|ESCALATED` | `RESPONDING` | P1 · Estado, bloque de resultado; P2 · badge | si es inválido se **deduce** de las entradas (nunca se inventa un éxito) |
| `action_type` | string\|null | `BLOCK_SOURCE_IP` | P2 · "Comando defensivo: …" | "Sin acción registrada" |
| `tool` | string\|null | `iptables / Wazuh Active Response` | P2 · Herramienta | no se muestra |
| `terminal_lines[]` | `{kind,timestamp,level,text}[]` | ver mock | P2 · terminal | vacío + `command_display` → "Comando previsto (aún no ejecutado)"; sin nada → aviso de que el backend no entregó comando |
| `verification_result` | `contained\|failed\|null` | `contained` | P1 · Verificación, y decide si el **último círculo se pone verde** y si aparece "Empresa protegida" | `null` → "Pendiente", círculo gris |
| `detected_at` | ISO 8601 UTC\|null | `2026-10-27T15:00:02Z` | P1 · Detectado | `—` |
| `response_started_at` | ISO 8601\|null | `…15:00:05Z` | **Solo viaja en el contrato/adaptador; la UI aún no lo pinta** (lo cubre el timeline con `entries[]`) | `null` |
| `response_finished_at` | ISO 8601\|null | `…15:00:08Z` | fin del tiempo transcurrido | si es `null` se usa el último `timestamp` recibido |
| `elapsed_time` | number (seg)\|null | `8` | **Solo respaldo** de "Tiempo transcurrido" cuando no hay timestamps utilizables | `--:--` |

## Cabecera del incidente (`DetectionPanel`)
| Variable frontend | Dato backend esperado | Tipo | Ejemplo |
|---|---|---|---|
| `ev.incident_id` | `incident.id` | string | `INC-077` |
| `ev.status` | `evidence.status` | enum | `CONTAINED` |
| `ev.server` | `incident.server_name` | string\|null | `srv-prod-01` |
| `ev.mitre_id / mitre_name / mitre_tactic` | `incident.mitre[0].technique_id / technique_name / tactic` | string\|null | `T1110 / Brute Force / Credential Access` |
| `ev.severity` | `incident.severity` | enum | `HIGH` |
| `ev.source_ip` | `event.source_ip` | string\|null | `192.168.56.50` |
| `ev.rule` | `evidence.rule` | string\|null | `CYBERSHIELD-RULE` |
| `ev.detected_at` | `incident.detected_at` | ISO 8601 UTC | `2026-10-27T15:00:02Z` |
| `ev.verification_result` | `response_action.verification_result` | `contained\|failed\|null` | `contained` |

## Consola, timeline y resultado (`DetectionPanel`)
| Variable frontend | Dato backend esperado | Tipo | Ejemplo / regla |
|---|---|---|---|
| `ev.entries[]` | `evidence[]` (una fila por evento) | array | vacío → "Sin registros de evidencia…" y botón de descarga deshabilitado |
| `entries[].timestamp` | `timestamp` | ISO 8601 UTC | inválido → `—` y el círculo **no** se colorea |
| `entries[].level` | `level` (propuesta) | `INFO\|OK\|WARN\|DENIED\|ERROR` | desconocido → `INFO` |
| `entries[].source` / `message` | `source` / `message` | string | `Wazuh` / `Regla aplicada: CYBERSHIELD-RULE` |
| `entries[].stage` | `stage` | `ATTACK_RECEIVED\|DETECTED\|RULE_APPLIED\|INCIDENT_CREATED\|RESPONDING\|CONTAINED\|FAILED\|ESCALATED` | stage desconocido → la entrada se descarta |
| `entries[].success` | `success` | boolean\|null | en `RESPONDING`, `true` = "Acción ejecutada" completada |
| `ev.outcomes[]` | `evidence.outcomes[]` `{label, detail}` | array | solo se muestran si `status=CONTAINED` **y** `verification_result=contained` |
| `response.failure_reason` | `response_action.failure_reason` (ya sanitizado) | string\|null | null → "El backend no entregó el motivo del fallo." |
| `response.notification` | `notification {channel,status}` | objeto\|null | `Telegram · Enviada`; null → no se muestra |

### Reglas de los 6 círculos (se calculan en `buildTimeline`, `evidenceUtils.ts`; todo sale de los datos)
| # | Círculo | Completado (color) cuando… | Mientras no | Si hay fallo |
|---|---|---|---|---|
| 1-4 | Ataque recibido · Evento detectado · Regla aplicada · Incidente creado | existe una entrada con ese `stage` **y** timestamp válido | gris | — |
| 5 | Acción ejecutada | una entrada `RESPONDING` trae `success=true` | **gris** (con pulso si ya inició: "en curso") | completado si se intentó y llegó FAILED/ESCALATED |
| 6 | Ataque bloqueado | entrada `CONTAINED` con timestamp **y** `verification_result="contained"` → **verde** | gris | `FAILED` → rojo "Respuesta fallida"; `ESCALATED` → ámbar. Nunca verde |

Hora relativa de cada círculo = `timestamp` de su entrada − primer `timestamp` (`--:--` si no hay). "Tiempo transcurrido" = primer `timestamp` → `response_finished_at` (o el último evento si aún no termina). Sin números fijos.

## Pantalla 2 · comando defensivo (`DefensiveCommandPanel`)
| Variable frontend | Dato backend esperado | Tipo | Ejemplo |
|---|---|---|---|
| `response.action_type` | `response_action.action_type` | string\|null | `BLOCK_SOURCE_IP` |
| `response.tool` | `response_action.tool` (propuesta) | string\|null | `iptables / Wazuh Active Response` |
| `response.terminal_lines[]` | `evidence.terminal_lines[]` `{kind: command\|output\|blank, timestamp, level, text}` | array | `root@srv-prod-01:~# sudo iptables -I INPUT -s 192.168.56.50 -j DROP` |
| `response.command_display` | `evidence.command_display` | string\|null | `sudo iptables -I INPUT -s … -j DROP` |
| `response.reason` | `response_action.reason` | string\|null | "Fuerza bruta (T1110) → bloquear IP de origen" |
| `ev.tools[]` | `evidence.tools[]` `{name, detail, role}` (o lista fija decidida por Giss) | array | `Wazuh / HIDS` |

El frontend **no contiene comandos de ningún ataque**: solo renderiza `terminal_lines` / `command_display` del incidente actual. Los diccionarios `eventLabel()` y `actionLabel()` (`evidenceUtils.ts`) son solo etiquetas; si el valor no está, se muestra el crudo.

## Estados → texto / color / ícono (una sola tabla)
`STATUS_VISUAL` y `STEP_VISUAL` en `src/components/evidence/evidenceUtils.ts`. Los componentes no escriben textos ni colores de estado por su cuenta; los colores están en `styles.css` (`.ev-t-in / .ev-t-wn / .ev-t-ok / .ev-t-er`).
| Estado | Texto | Tono | Ícono |
|---|---|---|---|
| DETECTED | Detectado | cian | FileText |
| RESPONDING | Respondiendo | ámbar | Clock |
| CONTAINED | Contenido | verde | Check |
| FAILED | Respuesta fallida | rojo | X |
| ESCALATED | Escalado | ámbar | AlertTriangle |

## Errores de API que la pantalla ya sabe manejar (hoy simulados con `?estado=`)
| Situación | Cómo se ve | Dónde se maneja | Probar con |
|---|---|---|---|
| Cargando | Esqueleto (`role=status`) | `EvidencePage.tsx` (`phase:"loading"`) | `?estado=cargando` |
| 404 / lista vacía | "Sin evidencia disponible para INC-xxx" | `phase:"empty"` | `?estado=vacio` |
| 500 / timeout / sin red | Aviso rojo con código + botón **Reintentar** | `phase:"error"` | `?estado=error` |
| JSON sin `incident_id` o no-objeto | "La respuesta del backend no trae incident_id…" | `adaptEvidencePayload` → `null` | `?estado=invalido` |
| `timestamp` inválido o ausente | `—` en consola, círculo gris, `--:--` | `adaptEvidence.ts` + `buildTimeline` | prueba unitaria |
| `stage` o `status` desconocido | entrada descartada / status deducido | `adaptEvidence.ts` | prueba unitaria |
| `action_type` o `command_display` nulos | "Sin acción registrada" / aviso de comando no entregado | `DefensiveCommandPanel` | `adaptEvidencePayload({incident_id:"X"})` |
| `mitre_id` nulo | "Sin clasificación MITRE confirmada" | `DetectionPanel` | idem |
| `failure_reason` nulo con FAILED | "El backend no entregó el motivo del fallo." | `DetectionPanel` | quitar `failure_reason` del payload `failed` en el mock |
| CONTAINED sin `verification_result` | Aviso "Contención sin verificar"; no "Empresa protegida"; último círculo gris | `DetectionPanel` + `buildTimeline` | prueba unitaria |

## Ejemplo mínimo de una entrada de `entries[]`
```json
{ "incident_id": "INC-077", "event_id": 1, "stage": "RESPONDING", "timestamp": "2026-10-27T15:00:06Z",
  "source": "Firewall", "level": "OK", "message": "Regla de bloqueo temporal aplicada (2 horas)",
  "action_type": "BLOCK_SOURCE_IP", "command_display": null, "result": "rule_inserted", "success": true }
```


---
# D3 · FAILED / ESCALATED, varios ataques con el MISMO componente

Un solo `DetectionPanel` + `DefensiveCommandPanel` muestra cualquier ataque. Lo que cambia es el JSON (`event_type`, `action_type`, `command_preview`, `terminal_lines`, `mitre_*`), no la pantalla. Mock: `?ataque=brute_force|ransomware&estado=detected|responding|contained|failed|escalated`.

## Variables nuevas o cambiadas en D3
| Variable frontend | Dato backend esperado | Tipo | Ejemplo | Fallback | Se muestra en |
|---|---|---|---|---|---|
| `response.command_preview` | `response_action.command_preview` | string\|null | `sudo iptables -I INPUT -s … -j DROP` | si falta usa `command_display`; si tampoco, "El backend no entregó un comando" | P2 · terminal / "Comando previsto" |
| `response.notification.notified` | `notification.sent` | boolean\|null | `true` | `null` → "Notificación móvil" (no se afirma que se avisó) | P1 · aviso móvil |
| `response.notification.{channel,status}` | `notification.{channel,status}` | string | `Telegram · Enviada al ingeniero de guardia` | sin notificación en FAILED/ESCALATED → "Sin dato de notificación móvil" | P1 |
| `scenario_note` | `incident.simulation_note` (opcional) | string\|null | "Simulación controlada: comportamiento compatible con ransomware…" | no se muestra | P1 · franja informativa |
| `response.failure_reason` | `response_action.failure_reason` (ya sanitizado) | string\|null | "El agente no confirmó que el proceso se detuviera…" | "El backend no entregó el motivo del fallo." | P1 (bloque rojo/ámbar) y P2 ("Error (sanitizado)") |
| `status` = `FAILED` \| `ESCALATED` | `incident.status` | enum | `ESCALATED` | si falta se deduce de `entries` | P1/P2 |

`action_status=failed` del documento equivale a `response.success=false` + `response.result="failed"` + entrada `FAILED` en `entries[]`. Confirmar el nombre real con César.

## Reglas del timeline en fallo (D3)
| Caso | Círculo 5 "Acción ejecutada" | Círculo 6 | Resultado |
|---|---|---|---|
| `FAILED`, nunca hubo `RESPONDING` con `success:true` | **rojo (fallido)** | **rojo** "Respuesta fallida / intervención requerida" | bloque rojo, "La empresa sigue en riesgo", comando intentado + error sanitizado |
| `ESCALATED` (después de `FAILED`) | rojo | **ámbar** "Escalado / intervención requerida" | bloque ámbar + "Ingeniero notificado" si `notified=true` |
| `RESPONDING` con éxito y luego falla la verificación | completo | rojo | igual que FAILED |
| `CONTAINED` + `verification_result=contained` | completo | verde | "Resultado de la contención" + "Empresa protegida" |
Nunca aparece "Empresa protegida" ni un círculo verde cuando el estado es FAILED/ESCALATED.

## Ataques del mock (todo viene de `ATTACKS` en `src/mocks/evidenceMock.ts`)
| Ataque | `event_type` | MITRE | `action_type` | `command_preview` |
|---|---|---|---|---|
| Fuerza bruta | `multiple_login_attempts` | T1110 Brute Force | `BLOCK_SOURCE_IP` | `sudo iptables -I INPUT -s 192.168.56.50 -j DROP` (mock) |
| Ransomware-like (simulación controlada) | `ransomware_like_behavior` | T1486 Data Encrypted for Impact | `STOP_PROCESS` | **placeholder** `[command_preview · lo entrega el backend…]` (no se inventa comando) |

Etiquetas de presentación para `event_type` / `action_type` nuevos: `EVENT_LABEL` y `ACTION_LABEL` en `evidenceUtils.ts` (una línea por tipo). Si el tipo no está, se muestra el valor crudo y la pantalla sigue funcionando. `06_defensive_command_planner.py` no venía en lo recibido; los nombres `STOP_PROCESS`, `CONTAIN_HOST`, `RESTRICT_DATA_FLOW`, etc. salen del diagrama del documento y **hay que confirmarlos** contra ese archivo.


---
# D4 · Mapeo del resto de la aplicación (frontend desacoplado)
**Punto único de datos de ejemplo:** `src/mocks/mockData.ts`. **Punto único de lectura:** funciones de `src/api/client.ts` y `src/services/management.ts` (misma firma que el cliente real; hoy devuelven el mock sin red). Los componentes no traen datos propios.
Lo que sigue lista variable visual ← dato backend esperado (mismos nombres que los comentarios `BACKEND_GISS`).

| Pantalla | Función | Variable frontend | Dato backend esperado | Tipo |
|---|---|---|---|---|
| Login / Registro | `login`, `register` | `user.id/name/email`, `token` | `user.{id,name,email}`, `token` | obj / string |
| Dashboard | `getDashboard` | `servidores, servidoresOnline, servidoresOffline, eventos, incidentes, criticos, estado` | `summary.{servers, servers_online, servers_offline, events, incidents, critical_incidents}` | number |
| Dashboard / Eventos | `getEvents` | `Evento.{id, createdAt, tipo, origen, severidad, estado, scope, serverId, serverName}` | `event.{id, created_at, event_type, source_ip, severity, estado, scope, server_id, server_name}` | `scope`: BLOCKED\|REACHED\|IMPACT |
| Dashboard | `getEventStats(window)` | `EventStats.{total_events, by_source[], by_type[], by_scope, by_server[], window_seconds}` | `stats.{total_events, by_source, by_type, by_scope, by_server, window_seconds}` | window: "1s"\|"60s" |
| Incidentes | `getIncidents` | `Incidente.{backendId, id, eventId, eventType, severidad, status, origen, servidor, detectado, asignado, reco, investigationSteps[], resolutionCriteria, mitre[], responseAction}` | `incident.{id, event_id, event_type, severity, status, source_ip, server_name, created_at, assigned_to, recommendation, investigation_steps, resolution_criteria, mitre_techniques, response_action}` | `status`: open\|investigating\|resolved |
| Incidentes | `updateIncidentStatus` | `(backendId, status)` | cambia `incident.status` | investigating\|resolved |
| Servidores | `getServers` | `ServerItem.{id, name, ipAddress, status, agent, createdAt, lastSeen}` | `server.{id, name, ip_address, status, agent, created_at, last_seen}` | `status`: online\|offline\|registered |
| Notificaciones | `getNotifications` | `NotificationItem.{id, incident_id, severity, recipient, channel, message, status, created_at, sent_at}` | `notification.*` (mismos nombres) | |
| Dispositivos | `getDevices` | `Device.{id, name, user, os, status, last_seen, mode}` | `device.{id, device_name, user, platform, status, last_seen, source_mode}` | status: trusted\|unauthorized\|unknown |
| Sesiones | `getSessions` | `SessionItem.{id, user, device, ip, started_at, status, mode}` | `session.{id, user, device, ip, started_at, status, source_mode}` | status: active\|revoked\|expired |
| Acciones | `getActions` | `ActionItem.{id, type, target, status, incident_id, created_at, reversible, mode}` | `response_action.{id, action_type, target, status, incident_id, created_at, reversible, source_mode}` | status: executed\|reverted\|failed\|pending |
| Protecciones | `getProtections` | `Protection.{id, name, sensor, description, mode, mitre[]}` | `control.{id, name, sensor, description, source_mode, mitre_techniques}` | mode: integrated\|simulated\|pending |
| Laboratorio | `getLabScenarios`, `runLabScenario` | `LabScenario.{…}` / `id` | `scenario.*` / ejecutar escenario `id` | |
| EmpresaDemo | (mock §9) | `ED_DEVICES[].trusted`, `ED_PROFILE.*` | decisión de Device Trust, usuario/sesión | clientes/documentos/reportes son contenido ficticio de la app demo |

Cambios de D4 respecto a D3: se eliminó `axios`, `src/api/endpoints.ts`, `.env.example` (`VITE_API_URL`), `src/data/mock.ts`, `src/mocks/management.ts` y `src/layout/Console.tsx` (código muerto no enrutado); el contenido de los mocks se unificó en `src/mocks/mockData.ts`.
