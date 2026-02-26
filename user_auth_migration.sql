-- Add authentication fields to existing users table.
-- Run once on your live database.

BEGIN;

ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS password_hash character varying(255);

COMMIT;
