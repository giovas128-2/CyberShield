-- CyberShield
-- P5: integridad referencial entre incidents y events
--
-- Evita que exista un incidente apuntando a un evento inexistente.
-- RESTRICT impide eliminar un evento mientras exista un incidente
-- asociado a él.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_incidents_event_id'
          AND conrelid = 'public.incidents'::regclass
    ) THEN
        ALTER TABLE public.incidents
        ADD CONSTRAINT fk_incidents_event_id
        FOREIGN KEY (event_id)
        REFERENCES public.events(id)
        ON DELETE RESTRICT;
    END IF;
END
$$;
