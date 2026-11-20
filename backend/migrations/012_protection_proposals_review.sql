-- CyberShield 2.0: propuestas SIN capacidad de ejecución.
-- Separadas de cybershield_protection_catalog, incidents y response_actions.
-- Aplicación manual después de validar pruebas y política de despliegue.
CREATE TABLE IF NOT EXISTS cybershield_protection_proposals (
    id BIGSERIAL PRIMARY KEY,
    technique_id VARCHAR(32) NOT NULL UNIQUE,
    technique_name TEXT NOT NULL,
    title TEXT NOT NULL,
    candidate_sensor TEXT NOT NULL,
    required_evidence TEXT NOT NULL,
    validation_plan TEXT NOT NULL,
    priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 5),
    status TEXT NOT NULL DEFAULT 'review_required'
        CHECK (status IN ('review_required', 'rejected', 'under_review')),
    generation_mode TEXT NOT NULL DEFAULT 'deterministic_template'
        CHECK (generation_mode = 'deterministic_template'),
    telemetry_verified BOOLEAN NOT NULL DEFAULT FALSE CHECK (telemetry_verified = FALSE),
    detection_verified BOOLEAN NOT NULL DEFAULT FALSE CHECK (detection_verified = FALSE),
    execution_allowed BOOLEAN NOT NULL DEFAULT FALSE CHECK (execution_allowed = FALSE),
    executed BOOLEAN NOT NULL DEFAULT FALSE CHECK (executed = FALSE),
    review_notes TEXT,
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_cybershield_proposals_status_priority
    ON cybershield_protection_proposals (status, priority, created_at);
