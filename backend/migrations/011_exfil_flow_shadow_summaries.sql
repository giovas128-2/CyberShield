-- CyberShield c6: resúmenes de inteligencia no ejecutables.
-- No crea incidentes, response_actions, ni modifica events existentes.
-- NO ejecutar todavía: revisar el esquema y su política de despliegue primero.
CREATE TABLE IF NOT EXISTS cybershield_exfil_flow_summaries (
    id BIGSERIAL PRIMARY KEY,
    sensor_id TEXT NOT NULL,
    flow_id TEXT NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    window_seconds INTEGER NOT NULL DEFAULT 300
        CHECK (window_seconds > 0),
    signature_id TEXT NOT NULL DEFAULT '1000002',
    observed_alerts BIGINT NOT NULL DEFAULT 0 CHECK (observed_alerts >= 0),
    distinct_observations BIGINT NOT NULL DEFAULT 0
        CHECK (distinct_observations >= 0),
    max_bytes_toserver BIGINT NOT NULL DEFAULT 0
        CHECK (max_bytes_toserver >= 0),
    bulk_transfer_observed BOOLEAN NOT NULL DEFAULT FALSE,
    evidence_fingerprint TEXT,
    technique_id TEXT NOT NULL DEFAULT 'T1041',
    control_id TEXT NOT NULL DEFAULT 'c6',
    decision_status TEXT NOT NULL DEFAULT 'simulation_only',
    mode TEXT NOT NULL DEFAULT 'shadow' CHECK (mode = 'shadow'),
    execution_allowed BOOLEAN NOT NULL DEFAULT FALSE
        CHECK (execution_allowed = FALSE),
    executed BOOLEAN NOT NULL DEFAULT FALSE
        CHECK (executed = FALSE),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ux_cybershield_exfil_sensor_flow_window
        UNIQUE (sensor_id, flow_id, window_start, window_seconds, signature_id)
);
CREATE INDEX IF NOT EXISTS ix_cybershield_exfil_flow_window
    ON cybershield_exfil_flow_summaries (window_start DESC);
