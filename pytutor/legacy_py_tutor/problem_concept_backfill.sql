-- Backfill concept tags for existing problems
-- Run this once on an already-seeded database.

BEGIN;

UPDATE public.problems
SET concept_id = 'CF4'
WHERE id IN (1, 2, 4, 5, 10, 13, 14);

UPDATE public.problems
SET concept_id = 'SM2'
WHERE id IN (6, 7, 8, 9, 16, 17, 18, 19);

UPDATE public.problems
SET concept_id = 'AM3'
WHERE id IN (3, 11, 12, 15);

COMMIT;
