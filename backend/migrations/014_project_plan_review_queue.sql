-- CyberShield: bandeja independiente de planes de seguridad por proyecto.
-- APLICAR SOLO TRAS VERIFICAR BASE DE PRUEBAS. No modifica controles c1–c8
-- ni las propuestas MITRE, respuestas, reglas o telemetría existentes.
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

CREATE TABLE IF NOT EXISTS public.cybershield_project_review_plans (
  id BIGSERIAL PRIMARY KEY,
  project_name VARCHAR(100) NOT NULL
    CHECK (length(btrim(project_name)) BETWEEN 1 AND 100),
  created_by INTEGER NOT NULL REFERENCES public.users(id),
  task_snapshot JSONB NOT NULL
    CHECK (jsonb_typeof(task_snapshot) = 'array'
       AND jsonb_array_length(task_snapshot) BETWEEN 1 AND 12),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.cybershield_project_review_tasks (
  id BIGSERIAL PRIMARY KEY,
  plan_id BIGINT NOT NULL REFERENCES public.cybershield_project_review_plans(id)
    ON DELETE RESTRICT,
  recommendation_id VARCHAR(55) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'review_required'
    CHECK (status IN ('review_required','under_review','planned','rejected')),
  reviewed_by INTEGER REFERENCES public.users(id),
  review_notes VARCHAR(2000),
  reviewed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_project_plan_recommendation UNIQUE (plan_id, recommendation_id)
);

CREATE TABLE IF NOT EXISTS public.cybershield_project_review_history (
  id BIGSERIAL PRIMARY KEY,
  task_id BIGINT NOT NULL REFERENCES public.cybershield_project_review_tasks(id)
    ON DELETE RESTRICT,
  actor_id INTEGER NOT NULL REFERENCES public.users(id),
  from_status VARCHAR(32) NOT NULL,
  to_status VARCHAR(32) NOT NULL
    CHECK (to_status IN ('under_review','planned','rejected')),
  notes VARCHAR(2000) NOT NULL CHECK (length(btrim(notes)) BETWEEN 10 AND 2000),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_cybershield_project_plans_created
  ON public.cybershield_project_review_plans(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_cybershield_project_tasks_status
  ON public.cybershield_project_review_tasks(status, plan_id);
CREATE INDEX IF NOT EXISTS ix_cybershield_project_history_task
  ON public.cybershield_project_review_history(task_id, created_at DESC);

COMMIT;
