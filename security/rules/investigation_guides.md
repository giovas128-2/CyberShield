# Guías de investigación de ciberseguridad — CyberShield

## Propósito

Este documento sirve como guía rápida para el analista cuando CyberShield detecta alguno de los siguientes eventos: `multiple_login_attempts`, `suspicious_file_change` o `suspicious_network_traffic`.

La idea no es asumir que cada alerta significa un ataque. Primero se revisa el contexto, después se reúne evidencia y, con base en eso, se decide si la actividad era válida, si requiere seguimiento o si ya se aplicó una mitigación. La investigación debe hacerse únicamente sobre sistemas y cuentas autorizados dentro del laboratorio o entorno correspondiente.

> **Nota sobre severidad:** las severidades indicadas aquí son criterios operativos para CyberShield. En Wazuh, los niveles de alerta son independientes y van de 0 a 16; una integración puede mapear la severidad de CyberShield a los niveles de Wazuh según la política del proyecto. Wazuh permite crear reglas personalizadas y definir condiciones por campos, frecuencia y ventana de tiempo. [Wazuh Documentation](https://documentation.wazuh.com/current/user-manual/ruleset/rules/custom.html)

---

## 1. Evento: `multiple_login_attempts`

### Qué significa

El sistema observó varios intentos de autenticación fallidos en un periodo corto. Esto puede ser algo tan sencillo como que una persona se equivocó varias veces al escribir su contraseña, pero también puede indicar un intento de acceso no autorizado. Por eso la alerta se investiga con contexto y no solo por cantidad.

### Qué revisar

- **IP de origen:** identificar desde qué dirección se hicieron los intentos y si pertenece a una red, equipo o usuario autorizado.
- **Usuario objetivo:** revisar qué cuenta recibió los intentos y si esa cuenta corresponde a una persona o servicio real.
- **Cantidad de intentos:** registrar cuántos fallos ocurrieron.
- **Ventana de tiempo:** anotar en cuánto tiempo ocurrieron. Cinco fallos en una hora no tienen el mismo peso que cinco en unos segundos.
- **Resultado posterior:** comprobar si después de los fallos hubo un inicio de sesión exitoso.
- **Origen habitual:** comparar con el comportamiento normal del usuario, por ejemplo, equipo conocido, horario habitual y red esperada.
- **Servicio involucrado:** revisar si fue SSH, RDP, una aplicación web, VPN u otro servicio de autenticación.
- **Cambios relacionados:** buscar cambios de contraseña, creación de cuentas, elevación de privilegios o accesos a recursos poco comunes después de la alerta.

### Evidencia relevante

La evidencia principal son los **logs de autenticación** del sistema o aplicación. También conviene guardar, cuando estén disponibles:

- Marca de tiempo de cada intento.
- Usuario objetivo.
- IP y, si existe, puerto de origen.
- Servicio de autenticación.
- Resultado de cada intento.
- Registro de un inicio de sesión exitoso posterior.
- Host o agente que generó el evento.
- Eventos de cambio de contraseña, privilegios o sesiones posteriores.

No basta con decir "hubo muchos intentos". La evidencia debe permitir reconstruir qué pasó, desde dónde y en qué secuencia.

### Recomendación

Primero validar si la IP, el usuario y el horario tienen una explicación normal. Si el origen pertenece a un usuario autorizado, puede tratarse de un error de autenticación o un problema operativo.

Si el origen no es reconocido, los intentos son muy rápidos o existe un inicio de sesión exitoso después de varios fallos, elevar la prioridad de la investigación. Según la política del laboratorio, se puede considerar un **bloqueo temporal**, forzar el cambio de credenciales, revisar sesiones activas o aplicar controles adicionales de autenticación. Cualquier bloqueo debe seguir la política del entorno para no afectar cuentas legítimas o servicios críticos.

### Criterio de resolución

El incidente se puede considerar resuelto cuando:

1. La actividad fue **validada como legítima**, o se determinó que era un error operativo conocido; **o**
2. Se aplicó la **mitigación correspondiente** cuando la actividad no era legítima.
3. Se revisaron los accesos posteriores relevantes y no aparece evidencia adicional de actividad anómala.
4. Durante la ventana de observación definida por la política no se repiten los intentos anómalos asociados al incidente.
5. Quedó registrada la justificación de cierre y la evidencia utilizada.

### Severidades típicas

- **Baja:** pocos fallos, separados en el tiempo, desde un origen conocido y sin señales adicionales.
- **Media:** varios fallos concentrados en una ventana corta o desde un origen no habitual, pero sin evidencia de acceso exitoso o impacto adicional.
- **Alta:** muchos intentos en poco tiempo, múltiples cuentas afectadas, origen no reconocido o inicio de sesión exitoso posterior que requiere validación.
- **Crítica:** además de lo anterior, existe evidencia clara de acceso no autorizado, compromiso de una cuenta privilegiada o actividad posterior que indique impacto serio.

---

## 2. Evento: `suspicious_file_change`

### Qué significa

El sistema detectó una modificación, creación, eliminación o cambio inesperado en un archivo o directorio que se considera relevante para seguridad. Ojo: que un archivo cambie no significa automáticamente que haya un incidente. Muchas aplicaciones actualizan archivos de manera normal; lo importante es saber si el cambio tenía sentido y quién o qué proceso lo realizó.

### Qué revisar

- **Ruta completa del archivo:** identificar exactamente qué archivo o directorio cambió.
- **Tipo de cambio:** determinar si fue creación, modificación, eliminación o cambio de atributos.
- **Fecha y hora:** revisar cuándo ocurrió y compararlo con ventanas de mantenimiento.
- **Usuario que realizó el cambio:** identificar la cuenta asociada, si el registro lo permite.
- **Proceso asociado:** revisar qué proceso o servicio produjo la modificación, cuando esa información exista.
- **Huella o hash:** comparar el hash anterior y el nuevo si el sistema de monitoreo lo proporciona.
- **Permisos y propietario:** comprobar si también cambiaron permisos, propietario o grupo.
- **Contexto del sistema:** verificar si el equipo estaba instalando actualizaciones, desplegando software, ejecutando una tarea programada o realizando mantenimiento.
- **Eventos relacionados:** buscar cambios de configuración, autenticaciones, ejecución de servicios o modificaciones en otros archivos cercanos en tiempo.

### Evidencia relevante

La evidencia debe incluir, como mínimo:

- Ruta del archivo.
- Tipo de cambio detectado.
- Marca de tiempo.
- Usuario y proceso, cuando estén disponibles.
- Hash anterior y actual, si existe.
- Propietario y permisos antes/después, cuando se puedan consultar.
- Registro de mantenimiento, actualización o despliegue que explique el cambio.
- Eventos del host alrededor del mismo momento.

Cuando sea posible, conservar los datos de forma que se pueda comprobar que la evidencia no fue alterada después de recolectarla.

### Recomendación

Primero confirmar si el cambio estaba planeado. Si coincide con una actualización, despliegue o tarea administrativa autorizada, documentar esa relación y evitar marcarlo como incidente real.

Si el cambio no tiene explicación, comparar el contenido o hash, identificar la cuenta y el proceso que hicieron la modificación y revisar si ocurrieron otros cambios relacionados. Si el archivo es sensible para la operación o seguridad del sistema, aplicar la política de contención correspondiente, por ejemplo restringir temporalmente el acceso al equipo afectado, recuperar una versión conocida o revertir el cambio cuando exista un procedimiento aprobado.

### Criterio de resolución

El incidente se considera resuelto cuando:

1. Se confirmó que el cambio era **legítimo y autorizado**, dejando evidencia del motivo; **o**
2. El cambio no autorizado fue **mitigado o revertido** siguiendo el procedimiento del entorno.
3. Se identificó la cuenta, proceso o actividad relacionada, en la medida que la evidencia disponible lo permita.
4. Se revisaron los cambios cercanos en tiempo y no quedan señales sin explicar.
5. El archivo o componente vuelve a un estado esperado o se aplicó la alternativa aprobada.
6. El cierre queda documentado con evidencia y responsable.

### Severidades típicas

- **Baja:** cambio en un archivo no crítico y con explicación operativa clara.
- **Media:** cambio inesperado en un archivo importante, pero sin señales adicionales de actividad maliciosa.
- **Alta:** modificación no autorizada en archivos sensibles, cambios de permisos o múltiples archivos relacionados.
- **Crítica:** cambios no autorizados en componentes críticos, repetición de modificaciones, afectación de cuentas privilegiadas o señales adicionales de compromiso del equipo.

---

## 3. Evento: `suspicious_network_traffic`

### Qué significa

CyberShield detectó tráfico de red que sale del comportamiento esperado o que merece una revisión. Puede ser una conexión perfectamente válida, por ejemplo una aplicación comunicándose con su servidor. La investigación busca distinguir entre tráfico normal, configuración incorrecta y actividad potencialmente peligrosa.

### Qué revisar

- **IP de origen y destino:** identificar quién inicia la comunicación y con qué equipo o servicio se comunica.
- **Puertos y protocolo:** registrar puerto de origen/destino y protocolo utilizado.
- **Dirección del flujo:** saber si es tráfico entrante, saliente o entre segmentos internos.
- **Frecuencia y duración:** observar cuántas conexiones hubo, cada cuánto y por cuánto tiempo.
- **Volumen aproximado:** revisar si el volumen está dentro de lo esperado para esa aplicación o equipo.
- **Destino habitual:** comprobar si el destino es conocido, autorizado y utilizado normalmente por el servicio.
- **Horario:** comparar la actividad con el horario normal del equipo o servicio.
- **Proceso o aplicación:** cuando los registros lo permitan, identificar qué proceso originó la conexión.
- **Eventos relacionados:** buscar autenticaciones, cambios de archivos, nuevas tareas o alertas del mismo host alrededor del evento.

### Evidencia relevante

- IP de origen.
- IP o nombre del destino.
- Puerto y protocolo.
- Marca de tiempo.
- Cantidad y duración de conexiones.
- Volumen de tráfico, si está disponible.
- Sensor, agente o dispositivo que registró el evento.
- Proceso o aplicación asociada, cuando exista.
- Reglas de firewall, proxy, IDS/IPS o registros de red que expliquen o contradigan la legitimidad del tráfico.
- Eventos del mismo host en la misma ventana de tiempo.

En una investigación de red, la secuencia importa mucho. Un solo registro aislado puede no decir gran cosa; varios eventos relacionados pueden explicar mejor el comportamiento.

### Recomendación

Validar primero si el destino y el servicio forman parte de la operación normal. Consultar inventario, documentación de aplicaciones, reglas de firewall y responsables del servicio antes de concluir que el tráfico es malicioso.

Si el destino no es conocido o el patrón es claramente anormal, revisar el equipo de origen, el proceso que genera la conexión y los eventos alrededor del mismo horario. Según la política, se puede restringir temporalmente la comunicación hacia el destino, ajustar una regla de monitoreo o aislar el equipo para investigación. La respuesta debe ser proporcional al nivel de evidencia y al impacto potencial.

### Criterio de resolución

El incidente se considera resuelto cuando:

1. El tráfico fue **validado como esperado** y se documentó su origen y propósito; **o**
2. Se aplicó la **mitigación autorizada** al tráfico o al equipo afectado.
3. Se verificó que no quedan conexiones anómalas activas o recurrentes relacionadas con el evento.
4. Se revisaron los eventos relevantes del host y no queda una señal crítica sin explicación.
5. Se documentó la decisión de cierre y la evidencia utilizada.

### Severidades típicas

- **Baja:** conexión poco común, pero con destino conocido y explicación operativa razonable.
- **Media:** tráfico anormal respecto al comportamiento del equipo o hacia un destino no habitual, sin evidencia adicional.
- **Alta:** conexiones repetitivas o sostenidas hacia destinos no autorizados, varios equipos afectados o señales adicionales de actividad sospechosa.
- **Crítica:** tráfico anómalo acompañado de evidencia de compromiso, afectación de sistemas críticos, cuentas privilegiadas o impacto significativo en el entorno.

---

## Flujo de investigación recomendado en la aplicación

Para los tres eventos, el botón **Investigar** puede mostrar la información en este orden:

**1. Identificar → 2. Revisar contexto → 3. Reunir evidencia → 4. Validar o mitigar → 5. Comprobar que no se repite → 6. Cerrar y documentar.**

Este flujo ayuda a que el analista no se vaya directo a bloquear algo sin entender primero qué pasó. En un entorno universitario, eso también hace que la investigación sea reproducible: otra persona puede revisar la alerta y llegar a una conclusión con la misma evidencia.

## Regla defensiva propuesta

Se propone **una sola regla nueva**: detectar conexiones salientes repetitivas desde el mismo equipo hacia un destino externo no habitual dentro de una ventana corta.

La regla busca encontrar un patrón que merezca investigación sin afirmar que el tráfico es malicioso por sí solo. El evento normalizado se guarda en `security/rules/new_rule.json`.

La lógica puede representarse en Wazuh mediante una regla de frecuencia/ventana de tiempo y un campo común, ya que Wazuh permite combinar coincidencias de eventos y condiciones como `frequency`, `timeframe` y `same_field`. citehttps://documentation.wazuh.com/current/user-manual/ruleset/rules.html

## Consideraciones de uso

- No cerrar una alerta solo porque "parece normal"; debe existir una justificación basada en evidencia.
- No bloquear automáticamente por una sola señal si la política del laboratorio no lo contempla.
- Correlacionar eventos del mismo host y de la misma ventana de tiempo para reducir falsos positivos.
- Registrar quién investigó, qué revisó, qué evidencia encontró y por qué se decidió cerrar o escalar.
- Mantener el alcance limitado a infraestructura autorizada y de laboratorio.
