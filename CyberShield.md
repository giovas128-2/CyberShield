# CyberShield

## 1. Descripción general del proyecto

**CyberShield** es una plataforma académica de ciberseguridad orientada al **monitoreo, detección, clasificación, correlación y respuesta defensiva** ante eventos e incidentes de seguridad dentro de un entorno controlado de laboratorio.

El sistema fue diseñado para demostrar, de forma visual y técnica, cómo una aplicación puede:

- recibir telemetría de diferentes fuentes,
- analizar eventos de seguridad,
- detectar comportamientos sospechosos,
- clasificar incidentes,
- asociarlos con tácticas y técnicas de **MITRE ATT&CK**,
- generar notificaciones,
- y ejecutar respuestas defensivas controladas y reversibles.

CyberShield no pretende ser un malware ni una herramienta ofensiva. Es un sistema de **defensa, monitoreo y respuesta** construido para fines académicos y de demostración.

---

## 2. ¿Para qué sirve CyberShield?

CyberShield sirve para:

1. **Monitorear eventos de seguridad** generados por un host, servicios o sensores.
2. **Detectar ataques o actividades sospechosas** mediante reglas y análisis de comportamiento.
3. **Correlacionar eventos** para evitar incidentes duplicados.
4. **Clasificar incidentes** según su severidad e impacto.
5. **Relacionar incidentes con MITRE ATT&CK** para dar contexto técnico.
6. **Ejecutar acciones defensivas automáticas o semiautomáticas** dentro del laboratorio autorizado.
7. **Registrar evidencia** para visualización en dashboard y seguimiento.
8. **Demostrar una arquitectura de seguridad** basada en detección, contención, rollback y trazabilidad.

---

## 3. Objetivo del proyecto

El objetivo principal de CyberShield es demostrar el flujo completo de un sistema de ciberseguridad:

**Detección → Análisis → Clasificación → Correlación → Respuesta → Verificación → Notificación**

De manera más específica, el proyecto busca:

- centralizar eventos de seguridad;
- transformar telemetría en incidentes utilizables;
- mostrar cómo se automatiza una respuesta defensiva;
- evidenciar la diferencia entre detección por firma, por sensor y por comportamiento;
- exponer visualmente el ciclo de protección de una aplicación de seguridad.

---

## 4. Alcance del sistema

CyberShield está pensado para un **entorno de laboratorio controlado y autorizado**.  
No está diseñado para usarse como una solución comercial lista para producción.

### Incluye:

- backend de seguridad;
- frontend para visualización;
- base de datos para persistencia;
- integración con Wazuh;
- simuladores de laboratorio;
- acciones defensivas controladas;
- pruebas de conectividad remota autorizada;
- correlación de incidentes;
- integración con MITRE ATT&CK.

### No incluye:

- explotación real de sistemas externos;
- ransomware real;
- ataques no autorizados;
- una infraestructura empresarial completa de SOC/SIEM/SOAR.

---

## 5. Herramientas y tecnologías utilizadas

## 5.1 Backend

- **Python**
- **FastAPI**
- **SQLAlchemy**
- **PostgreSQL**

El backend se encarga de:

- exponer endpoints de la API;
- recibir eventos;
- analizarlos;
- generar incidentes;
- guardar evidencia;
- crear notificaciones;
- crear y administrar acciones de respuesta.

---

## 5.2 Frontend

- **React**
- **TypeScript**
- **Vite**

El frontend permite visualizar:

- dashboard principal;
- eventos recientes;
- incidentes;
- notificaciones;
- acciones de respuesta;
- datos técnicos de evidencia;
- estado del sistema.

---

## 5.3 Sensores e integraciones

- **Wazuh**
- **Wazuh FIM (File Integrity Monitoring)**
- **Logs del sistema**
- **Forwarders personalizados**
- **HTTP remote-lab endpoint**
- **Bridges defensivos de respuesta**

---

## 5.4 Laboratorio y conectividad

- **WSL / Ubuntu**
- **Tailscale** (para conectividad entre equipos autorizados, cuando aplique)
- **Simuladores Python**
- **Curl / HTTP**
- **Entorno Linux para acciones defensivas**
- **Firewall local / reglas de red**
- **Cuentas de laboratorio**
- **Directorios controlados para simulación ransomware-like**

---

## 6. Arquitectura general de CyberShield

CyberShield está conformado por varios componentes que trabajan juntos:

1. **Fuentes de eventos**
   - Wazuh
   - logs del sistema
   - sensores
   - endpoint remoto autorizado
   - simuladores de laboratorio

2. **Backend**
   - recibe telemetría
   - la normaliza
   - la analiza
   - decide si crear evento, incidente, notificación y acción

3. **Base de datos**
   - guarda eventos
   - guarda incidentes
   - guarda notificaciones
   - guarda mapeos MITRE
   - guarda acciones de respuesta

4. **Frontend**
   - consume la API
   - presenta la información al usuario
   - muestra incidentes, evidencia y estado defensivo

5. **Bridges defensivos**
   - ejecutan acciones controladas y reversibles en el laboratorio

---

## 7. Diagrama de infraestructura

```mermaid
flowchart LR
    A[Equipo remoto autorizado] -->|HTTP / SSH / pruebas de laboratorio| B[Servidor monitoreado o laboratorio]
    B -->|Logs / FIM / eventos del host| C[Wazuh]
    C -->|Alertas| D[wazuh_forwarder.py]

    E[Simuladores controlados] --> F[Eventos locales / cambios en archivos]
    F --> C

    G[Cliente remoto de prueba] -->|POST /events/remote-lab| H[FastAPI Backend]

    D --> H

    H --> I[Motor de normalización]
    I --> J[Motor de reglas]
    J --> K[Correlación de incidentes]
    K --> L[Persistencia PostgreSQL]

    K --> M[MITRE ATT&CK Mapping]
    K --> N[Notificaciones]
    K --> O[Response Actions]

    O --> P[Response Bridges]
    P --> Q[Contención / bloqueo / restricción / rollback]

    R[Frontend React] -->|Consulta API| H
    H --> R
