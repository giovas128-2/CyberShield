-- CyberShield Intelligence
-- Migración 005: catálogo de conocimiento.
-- No ejecuta defensas ni activa reglas.

CREATE TABLE IF NOT EXISTS intelligence_sources (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    official_url TEXT NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    last_checked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS intelligence_threats (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL
        REFERENCES intelligence_sources(id),
    external_id VARCHAR(100) NOT NULL,
    name VARCHAR(250) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    reference_url TEXT,
    source_version VARCHAR(100),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (source_id, external_id)
);

CREATE TABLE IF NOT EXISTS intelligence_mitigations (
    id BIGSERIAL PRIMARY KEY,
    threat_id BIGINT NOT NULL
        REFERENCES intelligence_threats(id),
    name VARCHAR(250) NOT NULL,
    description TEXT NOT NULL,
    action_type VARCHAR(100),
    wazuh_rule_id VARCHAR(30),
    executor_name VARCHAR(100),
    verification_method TEXT,
    reversible BOOLEAN NOT NULL DEFAULT FALSE,
    approved_for_automation BOOLEAN NOT NULL
        DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS intelligence_sync_history (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL
        REFERENCES intelligence_sources(id),
    started_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMPTZ,
    status VARCHAR(30) NOT NULL,
    records_created INTEGER NOT NULL DEFAULT 0,
    records_updated INTEGER NOT NULL DEFAULT 0,
    error_summary TEXT
);

CREATE INDEX IF NOT EXISTS
    idx_intelligence_threats_category
ON intelligence_threats(category);

CREATE INDEX IF NOT EXISTS
    idx_intelligence_mitigations_threat
ON intelligence_mitigations(threat_id);

CREATE INDEX IF NOT EXISTS
    idx_intelligence_sync_history_source
ON intelligence_sync_history(source_id);
