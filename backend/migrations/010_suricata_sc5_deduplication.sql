-- Solo alertas SC5 nuevas con huella individual; no afecta históricos ni c6.
CREATE UNIQUE INDEX IF NOT EXISTS ux_events_suricata_sc5_fingerprint
ON events ((details->>'suricata_sc5_fingerprint'))
WHERE source = 'suricata'
  AND event_type = 'suspicious_network_traffic'
  AND details->>'suricata_sc5_fingerprint' IS NOT NULL;
