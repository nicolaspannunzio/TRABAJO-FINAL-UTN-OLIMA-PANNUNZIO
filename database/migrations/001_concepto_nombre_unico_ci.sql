BEGIN;
ALTER TABLE concepto DROP CONSTRAINT concepto_nombre_key;
CREATE UNIQUE INDEX uq_concepto_nombre_ci ON concepto (lower(nombre));
COMMIT;