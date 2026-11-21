-- CyberShield 2.0: auditoría de decisiones defensivas (modo shadow).
-- No instala defensas, ni modifica response_actions o incidentes.
BEGIN;
CREATE TABLE IF NOT EXISTS cybershield_autonomous_decisions (
    id BIGSERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL UNIQUE REFERENCES events(id) ON DELETE RESTRICT,
    technique_id VARCHAR(30) NOT NULL,
    control_id VARCHAR(70),
    recommended_action VARCHAR(60),
    target INET,
    decision_status VARCHAR(50) NOT NULL,
    reason TEXT NOT NULL,
    mode VARCHAR(20) NOT NULL DEFAULT 'shadow'
        CHECK (mode = 'shadow'),
    execution_allowed BOOLEAN NOT NULL DEFAULT FALSE
        CHECK (execution_allowed = FALSE),
    executed BOOLEAN NOT NULL DEFAULT FALSE
        CHECK (executed = FALSE),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cybershield_decisions_created
    ON cybershield_autonomous_decisions (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cybershield_decisions_status
    ON cybershield_autonomous_decisions (decision_status);
COMMIT;
