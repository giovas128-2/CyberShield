
BEGIN;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS role VARCHAR(20)
NOT NULL DEFAULT 'viewer';

UPDATE users
SET role = 'viewer'
WHERE role IS NULL;

ALTER TABLE users
DROP CONSTRAINT IF EXISTS users_role_check;

ALTER TABLE users
ADD CONSTRAINT users_role_check
CHECK (role IN ('admin', 'engineer', 'viewer'));

COMMIT;
