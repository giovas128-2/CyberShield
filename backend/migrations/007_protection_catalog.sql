-- CyberShield 007: catálogo persistente de protecciones
-- La migración no crea, habilita ni ejecuta respuestas automáticas.
-- Ejecutar UNA sola vez desde el entorno PostgreSQL del laboratorio.
BEGIN;

CREATE TABLE IF NOT EXISTS cybershield_protection_catalog (
    control_id VARCHAR(70) PRIMARY KEY,
    name VARCHAR(160) NOT NULL,
    sensor VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    mode VARCHAR(20) NOT NULL
       CHECK (mode IN ('integrated', 'simulated', 'pending')),
    origin VARCHAR(20) NOT NULL
       CHECK (origin IN ('builtin', 'proposal')),
    mitre_techniques JSONB NOT NULL DEFAULT '[]'::jsonb
       CHECK (jsonb_typeof(mitre_techniques) = 'array'),
    execution_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    execution_verified BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER NOT NULL DEFAULT 1000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT proposals_must_be_pending
      CHECK (origin <> 'proposal'
        OR (mode = 'pending' AND NOT execution_enabled AND NOT execution_verified)),
    CONSTRAINT no_unverified_execution
      CHECK (NOT execution_enabled OR execution_verified)
);

-- La plataforma existente conserva sus ocho defensas y flujos de respuesta
-- independientes; este nuevo catálogo NO los ejecuta.
INSERT INTO cybershield_protection_catalog
 (control_id, name, sensor, description, mode, origin,
  mitre_techniques, sort_order, execution_enabled, execution_verified)
VALUES
  ('c1', 'Fuerza bruta', 'Wazuh', 'Monitoreo con respuesta segura y reversible en el laboratorio.', 'integrated', 'builtin', '[{"technique_id":"T1110","technique_name":"Brute Force","tactic":"Credential Access","is_primary":true}]'::jsonb, 1, FALSE, FALSE),
  ('c2', 'Dispositivo no autorizado', 'Aplicación', 'Device Trust validado con backend, PostgreSQL y frontend.', 'integrated', 'builtin', '[{"technique_id":"T1078","technique_name":"Valid Accounts","tactic":"Defense Evasion","is_primary":true}]'::jsonb, 2, FALSE, FALSE),
  ('c3', 'Cambio de archivo crítico', 'Wazuh FIM', 'Detección FIM validada de extremo a extremo en el laboratorio.', 'integrated', 'builtin', '[{"technique_id":"T1565.001","technique_name":"Stored Data Manipulation","tactic":"Impact","is_primary":true}]'::jsonb, 3, FALSE, FALSE),
  ('c4', 'Abuso de privilegios', 'Wazuh', 'Caso validado mediante evento controlado de elevación de privilegios.', 'integrated', 'builtin', '[{"technique_id":"T1548.003","technique_name":"Sudo and Sudo Caching","tactic":"Privilege Escalation","is_primary":true}]'::jsonb, 4, FALSE, FALSE),
  ('c5', 'Conexión externa sospechosa', 'Suricata', 'Telemetría y alerta real de Suricata integradas con FastAPI y PostgreSQL.', 'integrated', 'builtin', '[{"technique_id":"T1041","technique_name":"Exfiltration Over C2 Channel","tactic":"Exfiltration","is_primary":true}]'::jsonb, 5, FALSE, FALSE),
  ('c6', 'Posible exfiltración de datos', 'Suricata + App', 'Escenario defensivo con datos ficticios; no implica exfiltración confirmada.', 'simulated', 'builtin', '[{"technique_id":"T1041","technique_name":"Exfiltration Over C2 Channel","tactic":"Exfiltration","is_primary":true}]'::jsonb, 6, FALSE, FALSE),
  ('c7', 'Comportamiento tipo ransomware', 'Wazuh', 'Patrón benigno de modificaciones masivas; no utiliza malware ni cifrado real.', 'simulated', 'builtin', '[{"technique_id":"T1486","technique_name":"Data Encrypted for Impact","tactic":"Impact","is_primary":true}]'::jsonb, 7, FALSE, FALSE),
  ('c8', 'Posible movimiento lateral', 'Wazuh + Suricata', 'Conexión SSH autorizada entre hosts del laboratorio; clasificación contextual.', 'simulated', 'builtin', '[{"technique_id":"T1021.004","technique_name":"Remote Services: SSH","tactic":"Lateral Movement","is_primary":true}]'::jsonb, 8, FALSE, FALSE)
ON CONFLICT (control_id) DO NOTHING;

COMMIT;
