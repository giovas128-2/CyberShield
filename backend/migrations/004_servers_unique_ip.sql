-- CyberShield
-- Migracion 004: unicidad de IP de servidores
-- Fase 3 - Infraestructura de Yahir
--
-- Requisitos:
-- 1. La tabla public.servers debe existir.
-- 2. No deben existir IP duplicadas.
-- 3. Verificar que no exista previamente el indice.
--
-- No elimina ni actualiza servidores.
-- Revisar compatibilidad con entornos multiorganizacion.

BEGIN;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM public.servers
        GROUP BY ip_address
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION
            'Existen direcciones IP duplicadas';
    END IF;
END;
$$;

CREATE UNIQUE INDEX cs_servers_ip_unique
ON public.servers (ip_address);

COMMIT;
