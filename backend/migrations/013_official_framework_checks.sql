-- CyberShield: seguimiento documental de fuentes oficiales.
-- Almacena solamente versiones, firmas y fechas de consulta.
-- No modifica protecciones, incidentes, respuestas ni reglas activas.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

CREATE TABLE IF NOT EXISTS public.intelligence_official_framework_checks (
    source_key VARCHAR(16) PRIMARY KEY
        CHECK (source_key IN ('mitre', 'nist', 'cis', 'cisa')),
    name VARCHAR(120) NOT NULL,
    official_url TEXT NOT NULL,
    baseline_version VARCHAR(100),
    observed_version VARCHAR(100),
    baseline_fingerprint CHAR(64),
    observed_fingerprint CHAR(64),
    status VARCHAR(24) NOT NULL DEFAULT 'not_checked'
        CHECK (status IN ('not_checked', 'verified', 'unavailable')),
    needs_review BOOLEAN NOT NULL DEFAULT FALSE,
    record_count INTEGER,
    last_checked_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    last_changed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK ((baseline_fingerprint IS NULL) = (baseline_version IS NULL)),
    CHECK ((observed_fingerprint IS NULL) = (observed_version IS NULL))
);
COMMIT;
