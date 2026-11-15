-- =====================================================================
-- seed_demo.sql - Datos semilla para la demo (tarea F0-03)
-- Sistema de asistencia para preliquidacion de alquileres
-- =====================================================================
-- Requisitos previos:
--   1. esquema_completo.sql aplicado (14 tablas, roles 'admin' y 'operador').
--   2. Al menos un usuario con rol 'admin' en la tabla usuario (F0-02).
--      Se usa como cargado_por de los importes del periodo anterior.
--   3. Base limpia: si la semilla ya existe, el script aborta. Para volver a
--      cargarla en un ensayo, ejecutar antes reset_demo.sql.
--
-- Contenido (todos los datos son FICTICIOS, sin nombres, CUIT, DNI ni
-- direcciones reales):
--   * 1 propiedad anonimizada con 2 copropietarios al 50/50 (suman 100).
--   * Catalogo de 7 conceptos; 'Expensas' tiene umbral propio de 50 %.
--   * Plantilla de la propiedad con 6 conceptos, 'API' inactivo.
--     'Seguro' queda solo en el catalogo (no esta en la plantilla).
--   * Periodo anterior (2026-08-01) con checklist e importes, pensado para
--     los casos de HU-10 al cargar el periodo de la demo (2026-09-01):
--
--       Concepto            Ago 2026         Carga sugerida Sep  Resultado esperado
--       ------------------  ---------------  ------------------  ---------------------------
--       TGI                 1000.00          1350.00 (35 %)      variacion_inusual (umbral 30)
--       Expensas            1000.00          1350.00 (35 %)      sin advertencia (umbral 50)
--       EPE                 1000.00          -200.00 (120 %)     variacion_inusual
--       Aguas Santafesinas  0.00             cualquier valor     sin_referencia (anterior 0)
--       Litoral Gas         no_corresponde   cualquier valor     sin_referencia (sin importe)
--       API                 (inactivo)       -                   no aparece en el checklist
--
--   * No se siembran preliquidaciones: son snapshots inmutables y la demo
--     final debe partir de un periodo sin preliquidaciones.
--
-- Los ids son UUID fijos para que el script sea reproducible y para poder
-- referenciarlos en pruebas manuales.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- Controles previos: falla con un mensaje claro en vez de dejar datos a medias
-- ---------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM usuario u
        JOIN rol r ON r.id = u.rol_id
        WHERE r.nombre = 'admin' AND u.activo
    ) THEN
        RAISE EXCEPTION 'No hay un usuario admin activo en la tabla usuario. Crearlo primero (F0-02).';
    END IF;

    IF EXISTS (SELECT 1 FROM propiedad WHERE id = 'd1000000-0000-4000-8000-000000000001')
       OR EXISTS (SELECT 1 FROM concepto WHERE nombre IN
                  ('TGI', 'Aguas Santafesinas', 'API', 'Litoral Gas', 'EPE', 'Expensas', 'Seguro')) THEN
        RAISE EXCEPTION 'La semilla (o conceptos con el mismo nombre) ya existe. Ejecutar reset_demo.sql antes de volver a sembrar.';
    END IF;
END;
$$;

-- ---------------------------------------------------------------------
-- Propiedad y propietarios (HU-03, HU-04)
-- ---------------------------------------------------------------------
INSERT INTO propiedad (id, direccion, localidad, estado) VALUES
    ('d1000000-0000-4000-8000-000000000001', 'Calle Ficticia 1234, Depto 2B', 'Localidad Demo', 'activa');

-- CUIT de ejemplo con prefijo 99 (no asignable a personas reales).
-- Emails en el dominio reservado example.com.
INSERT INTO propietario (id, nombre, cuit_dni, email, estado, telefono) VALUES
    ('d2000000-0000-4000-8000-000000000001', 'Propietaria Demo A', '99-00000001-0',
     'propietaria.a@example.com', 'activa', '000-000-0001'),
    ('d2000000-0000-4000-8000-000000000002', 'Propietario Demo B', '99-00000002-0',
     'propietario.b@example.com', 'activa', '000-000-0002');

-- Reparto 50/50: en la demo se cambia a 60/40 y se intenta guardar 90 (HU-04).
INSERT INTO propiedad_propietario (id, propiedad_id, propietario_id, porcentaje) VALUES
    ('d3000000-0000-4000-8000-000000000001', 'd1000000-0000-4000-8000-000000000001',
     'd2000000-0000-4000-8000-000000000001', 50.00),
    ('d3000000-0000-4000-8000-000000000002', 'd1000000-0000-4000-8000-000000000001',
     'd2000000-0000-4000-8000-000000000002', 50.00);

-- ---------------------------------------------------------------------
-- Catalogo de conceptos (HU-05)
-- umbral_variacion_pct NULL = usa el umbral global del backend (30 %).
-- ---------------------------------------------------------------------
INSERT INTO concepto (id, nombre, tipo, umbral_variacion_pct) VALUES
    ('d4000000-0000-4000-8000-000000000001', 'TGI',                'impuesto municipal',  NULL),
    ('d4000000-0000-4000-8000-000000000002', 'Aguas Santafesinas', 'servicio',            NULL),
    ('d4000000-0000-4000-8000-000000000003', 'API',                'impuesto provincial', NULL),
    ('d4000000-0000-4000-8000-000000000004', 'Litoral Gas',        'servicio',            NULL),
    ('d4000000-0000-4000-8000-000000000005', 'EPE',                'servicio',            NULL),
    ('d4000000-0000-4000-8000-000000000006', 'Expensas',           'expensas',            50.00),
    ('d4000000-0000-4000-8000-000000000007', 'Seguro',             'seguro',              NULL);

-- ---------------------------------------------------------------------
-- Plantilla de la propiedad (HU-06): API queda inactivo
-- ---------------------------------------------------------------------
INSERT INTO concepto_propiedad (id, propiedad_id, concepto_id, activo) VALUES
    ('d5000000-0000-4000-8000-000000000001', 'd1000000-0000-4000-8000-000000000001',
     'd4000000-0000-4000-8000-000000000001', TRUE),   -- TGI
    ('d5000000-0000-4000-8000-000000000002', 'd1000000-0000-4000-8000-000000000001',
     'd4000000-0000-4000-8000-000000000002', TRUE),   -- Aguas Santafesinas
    ('d5000000-0000-4000-8000-000000000003', 'd1000000-0000-4000-8000-000000000001',
     'd4000000-0000-4000-8000-000000000003', FALSE),  -- API (inactivo)
    ('d5000000-0000-4000-8000-000000000004', 'd1000000-0000-4000-8000-000000000001',
     'd4000000-0000-4000-8000-000000000004', TRUE),   -- Litoral Gas
    ('d5000000-0000-4000-8000-000000000005', 'd1000000-0000-4000-8000-000000000001',
     'd4000000-0000-4000-8000-000000000005', TRUE),   -- EPE
    ('d5000000-0000-4000-8000-000000000006', 'd1000000-0000-4000-8000-000000000001',
     'd4000000-0000-4000-8000-000000000006', TRUE);   -- Expensas

-- ---------------------------------------------------------------------
-- Periodo anterior 2026-08-01: checklist cerrado (solo conceptos activos)
-- ---------------------------------------------------------------------
INSERT INTO checklist_periodo (propiedad_id, periodo, concepto_propiedad_id, estado) VALUES
    ('d1000000-0000-4000-8000-000000000001', DATE '2026-08-01', 'd5000000-0000-4000-8000-000000000001', 'cargado'),        -- TGI
    ('d1000000-0000-4000-8000-000000000001', DATE '2026-08-01', 'd5000000-0000-4000-8000-000000000002', 'cargado'),        -- Aguas ($0)
    ('d1000000-0000-4000-8000-000000000001', DATE '2026-08-01', 'd5000000-0000-4000-8000-000000000004', 'no_corresponde'), -- Litoral Gas
    ('d1000000-0000-4000-8000-000000000001', DATE '2026-08-01', 'd5000000-0000-4000-8000-000000000005', 'cargado'),        -- EPE
    ('d1000000-0000-4000-8000-000000000001', DATE '2026-08-01', 'd5000000-0000-4000-8000-000000000006', 'cargado');        -- Expensas

-- ---------------------------------------------------------------------
-- Importes del periodo anterior (referencia para HU-10)
-- cargado_por: el primer admin activo (orden determinista por id).
-- ---------------------------------------------------------------------
INSERT INTO importe_mensual (concepto_propiedad_id, periodo, importe, cargado_por)
SELECT v.concepto_propiedad_id::uuid, DATE '2026-08-01', v.importe, admin.id
FROM (VALUES
        ('d5000000-0000-4000-8000-000000000001', 1000.00),  -- TGI
        ('d5000000-0000-4000-8000-000000000002',    0.00),  -- Aguas Santafesinas (anterior 0)
        ('d5000000-0000-4000-8000-000000000005', 1000.00),  -- EPE
        ('d5000000-0000-4000-8000-000000000006', 1000.00)   -- Expensas
     ) AS v (concepto_propiedad_id, importe)
CROSS JOIN (
    SELECT u.id
    FROM usuario u
    JOIN rol r ON r.id = u.rol_id
    WHERE r.nombre = 'admin' AND u.activo
    ORDER BY u.id
    LIMIT 1
) AS admin;

-- ---------------------------------------------------------------------
-- Control final: los porcentajes de la propiedad suman 100
-- ---------------------------------------------------------------------
DO $$
DECLARE
    v_suma NUMERIC(6,2);
BEGIN
    SELECT SUM(porcentaje) INTO v_suma
    FROM propiedad_propietario
    WHERE propiedad_id = 'd1000000-0000-4000-8000-000000000001';

    IF v_suma IS DISTINCT FROM 100.00 THEN
        RAISE EXCEPTION 'El reparto de la propiedad semilla suma % en lugar de 100', v_suma;
    END IF;
END;
$$;

COMMIT;

-- ---------------------------------------------------------------------
-- Verificacion rapida (opcional, solo lectura)
-- ---------------------------------------------------------------------
-- SELECT c.nombre, cp.activo, cl.estado, im.importe, c.umbral_variacion_pct
-- FROM concepto_propiedad cp
-- JOIN concepto c ON c.id = cp.concepto_id
-- LEFT JOIN checklist_periodo cl ON cl.concepto_propiedad_id = cp.id AND cl.periodo = DATE '2026-08-01'
-- LEFT JOIN importe_mensual  im ON im.concepto_propiedad_id = cp.id AND im.periodo = DATE '2026-08-01'
-- WHERE cp.propiedad_id = 'd1000000-0000-4000-8000-000000000001'
-- ORDER BY c.nombre;
