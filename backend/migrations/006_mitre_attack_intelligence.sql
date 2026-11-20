-- CyberShield Intelligence
-- Migración 006: MITRE ATT&CK Enterprise
-- No activa acciones defensivas.

CREATE TABLE intelligence_mitre_techniques (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL
        REFERENCES intelligence_sources(id),
    stix_id VARCHAR(150) NOT NULL UNIQUE,
    attack_id VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(250) NOT NULL,
    description TEXT,
    is_subtechnique BOOLEAN NOT NULL DEFAULT FALSE,
    source_version VARCHAR(100),
    modified_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE intelligence_mitre_mitigations (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL
        REFERENCES intelligence_sources(id),
    stix_id VARCHAR(150) NOT NULL UNIQUE,
    mitigation_id VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(250) NOT NULL,
    description TEXT,
    source_version VARCHAR(100),
    modified_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE intelligence_mitre_relationships (
    id BIGSERIAL PRIMARY KEY,
    stix_id VARCHAR(150) NOT NULL UNIQUE,
    technique_id BIGINT NOT NULL
        REFERENCES intelligence_mitre_techniques(id),
    mitigation_id BIGINT NOT NULL
        REFERENCES intelligence_mitre_mitigations(id),
    relationship_type VARCHAR(50) NOT NULL
        DEFAULT 'mitigates',
    CHECK (relationship_type = 'mitigates'),
    UNIQUE (technique_id, mitigation_id)
);

CREATE INDEX idx_mitre_technique_source
ON intelligence_mitre_techniques(source_id);

CREATE INDEX idx_mitre_mitigation_source
ON intelligence_mitre_mitigations(source_id);

CREATE INDEX idx_mitre_relationship_technique
ON intelligence_mitre_relationships(technique_id);

CREATE INDEX idx_mitre_relationship_mitigation
ON intelligence_mitre_relationships(mitigation_id);
