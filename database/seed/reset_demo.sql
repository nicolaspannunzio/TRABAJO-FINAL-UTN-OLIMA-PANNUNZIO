-- =====================================================================
-- reset_demo.sql - Reinicio de datos para ENSAYO de la demo (tarea F0-03)
-- Sistema de asistencia para preliquidacion de alquileres
-- =====================================================================
--
--   !!! SOLO PARA ENSAYO !!!
--
--   Este script DESHABILITA temporalmente los triggers de inmutabilidad
--   para borrar preliquidaciones, que son snapshots que el sistema nunca
--   permite modificar ni borrar. Por eso:
--     * NO usarlo en los tests automaticos (usan una base descartable).
--     * NO ejecutarlo contra el proyecto Supabase una vez que empieza el
--       ensayo final de la demo (F0-06). La demo final usa un periodo
--       que todavia no tiene preliquidaciones.
--     * NUNCA ejecutarlo en una base con datos reales.
--
-- Que hace:
--   * Borra TODOS los datos del dominio: preliquidaciones (con detalle,
--     advertencias y reparto), importes, checklists, plantillas, catalogo,
--     propietarios, propiedades y auditoria.
--   * Conserva rol y usuario (las cuentas viven tambien en auth.users).
--   * Vuelve a habilitar los triggers antes del COMMIT. Si algo falla, el
--     ROLLBACK deja los triggers como estaban (ALTER TABLE es transaccional).
--
-- Despues de ejecutarlo, correr seed_demo.sql para recargar la semilla.
--
-- Confirmacion obligatoria: descomentar la linea SET de abajo. Sin ella el
-- script aborta sin tocar nada.
-- =====================================================================

-- SET demo.permitir_reset = 'si';

BEGIN;

DO $$
BEGIN
    IF COALESCE(current_setting('demo.permitir_reset', true), '') <> 'si' THEN
        RAISE EXCEPTION 'reset_demo.sql es solo para ensayo. Descomentar "SET demo.permitir_reset = ''si'';" para confirmar.';
    END IF;
END;
$$;

-- ---------------------------------------------------------------------
-- 1. Deshabilitar los triggers de inmutabilidad (solo esta transaccion)
-- ---------------------------------------------------------------------
ALTER TABLE reparto                    DISABLE TRIGGER tg_reparto_inmutable;
ALTER TABLE reparto                    DISABLE TRIGGER tg_reparto_sin_truncate;
ALTER TABLE preliquidacion_advertencia DISABLE TRIGGER tg_preliquidacion_advertencia_inmutable;
ALTER TABLE preliquidacion_advertencia DISABLE TRIGGER tg_preliquidacion_advertencia_sin_truncate;
ALTER TABLE preliquidacion_detalle     DISABLE TRIGGER tg_preliquidacion_detalle_inmutable;
ALTER TABLE preliquidacion_detalle     DISABLE TRIGGER tg_preliquidacion_detalle_sin_truncate;
ALTER TABLE preliquidacion             DISABLE TRIGGER tg_preliquidacion_inmutable;
ALTER TABLE preliquidacion             DISABLE TRIGGER tg_preliquidacion_sin_truncate;

-- ---------------------------------------------------------------------
-- 2. Borrar datos en orden de dependencias (hijos antes que padres)
-- Se usa DELETE y no TRUNCATE para respetar las FK sin CASCADE.
-- ---------------------------------------------------------------------
DELETE FROM reparto;
DELETE FROM preliquidacion_advertencia;
DELETE FROM preliquidacion_detalle;
DELETE FROM preliquidacion;

DELETE FROM importe_mensual;
DELETE FROM checklist_periodo;
DELETE FROM concepto_propiedad;
DELETE FROM propiedad_propietario;
DELETE FROM concepto;
DELETE FROM propietario;
DELETE FROM propiedad;

DELETE FROM auditoria;

-- ---------------------------------------------------------------------
-- 3. Volver a habilitar los triggers de inmutabilidad
-- ---------------------------------------------------------------------
ALTER TABLE reparto                    ENABLE TRIGGER tg_reparto_inmutable;
ALTER TABLE reparto                    ENABLE TRIGGER tg_reparto_sin_truncate;
ALTER TABLE preliquidacion_advertencia ENABLE TRIGGER tg_preliquidacion_advertencia_inmutable;
ALTER TABLE preliquidacion_advertencia ENABLE TRIGGER tg_preliquidacion_advertencia_sin_truncate;
ALTER TABLE preliquidacion_detalle     ENABLE TRIGGER tg_preliquidacion_detalle_inmutable;
ALTER TABLE preliquidacion_detalle     ENABLE TRIGGER tg_preliquidacion_detalle_sin_truncate;
ALTER TABLE preliquidacion             ENABLE TRIGGER tg_preliquidacion_inmutable;
ALTER TABLE preliquidacion             ENABLE TRIGGER tg_preliquidacion_sin_truncate;

-- Control: los 8 triggers deben quedar habilitados antes de confirmar.
DO $$
DECLARE
    v_deshabilitados INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_deshabilitados
    FROM pg_trigger
    WHERE tgname IN ('tg_reparto_inmutable', 'tg_reparto_sin_truncate',
                     'tg_preliquidacion_advertencia_inmutable', 'tg_preliquidacion_advertencia_sin_truncate',
                     'tg_preliquidacion_detalle_inmutable', 'tg_preliquidacion_detalle_sin_truncate',
                     'tg_preliquidacion_inmutable', 'tg_preliquidacion_sin_truncate')
      AND tgenabled = 'D';

    IF v_deshabilitados > 0 THEN
        RAISE EXCEPTION 'Quedaron % triggers de inmutabilidad deshabilitados; se cancela el reinicio', v_deshabilitados;
    END IF;
END;
$$;

COMMIT;

RESET demo.permitir_reset;
