-- Migración 001: nombre de concepto único sin distinguir mayúsculas ('TGI' y 'tgi').
-- esquema_completo.sql ya incluye este índice. La migración es idempotente:
-- en una base nueva no cambia nada y se puede ejecutar sin error.
BEGIN;
ALTER TABLE concepto DROP CONSTRAINT IF EXISTS concepto_nombre_key;
CREATE UNIQUE INDEX IF NOT EXISTS uq_concepto_nombre_ci ON concepto (lower(nombre));
COMMIT;
