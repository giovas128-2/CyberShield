-- CyberShield
-- Migracion: credenciales individuales de agentes
-- Fase 3 - Infraestructura
--
-- Ejecutar solo despues de validar el entorno.
-- No modifica las tablas servers ni server_enrollments.
-- El script falla si la tabla ya existe.

BEGIN;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

CREATE TABLE public.server_agent_credentials (
    agent_id UUID PRIMARY KEY,

    server_id INTEGER NOT NULL
        REFERENCES public.servers(id),

    token_hash CHAR(64) NOT NULL UNIQUE,

    platform VARCHAR(64) NOT NULL,
    agent_version VARCHAR(32) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    last_seen TIMESTAMPTZ,

    revoked_at TIMESTAMPTZ,

    CONSTRAINT cs_agent_revocation_date
        CHECK (
            revoked_at IS NULL
            OR revoked_at >= created_at
        ),

    CONSTRAINT cs_agent_token_hash_format
        CHECK (
            token_hash ~ '^[0-9a-f]{64}$'
        )
);

CREATE UNIQUE INDEX cs_agent_active_server
ON public.server_agent_credentials(server_id)
WHERE revoked_at IS NULL;

COMMIT;
