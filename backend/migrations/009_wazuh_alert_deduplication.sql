-- CyberShield 009: idempotencia de eventos de Wazuh.
-- Una alerta de Wazuh con ID se acepta una sola vez en events.
-- El índice se comprueba durante el INSERT inicial, ANTES de incidentes y acciones.
-- No elimina ni actualiza eventos anteriores.
BEGIN;

CREATE UNIQUE INDEX IF NOT EXISTS ux_events_wazuh_alert_id
ON events ((details->>'wazuh_alert_id'))
WHERE source = 'wazuh'
  AND details ? 'wazuh_alert_id';

COMMIT;
