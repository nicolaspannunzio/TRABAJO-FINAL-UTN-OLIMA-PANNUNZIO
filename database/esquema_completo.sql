-- =====================================================================
-- Sistema de asistencia para preliquidacion de alquileres
-- Script de creacion de base de datos (PostgreSQL / Supabase)
-- Modelo corregido (posterior a la 2da devolucion del tutor)
-- =====================================================================
-- Convenciones:
--   * ids UUID generados con gen_random_uuid() (PostgreSQL 13+ y Supabase),
--     salvo usuario.id, que es el mismo UUID de Supabase Auth (auth.users.id).
--   * periodo (DATE): primer dia del mes (ej. 2026-09-01). Se fuerza con un
--     CHECK en cada tabla que tiene la columna.
--   * importes NUMERIC(14,2); porcentajes NUMERIC(5,2).
--   * Los importes pueden ser negativos (notas de credito): no hay CHECK de signo.
--
-- Seguridad (estrategia RLS "A"):
--   * RLS esta ACTIVADA en todas las tablas y NO se define ninguna policy.
--     Resultado: los roles anon y authenticated no pueden leer ni escribir
--     nada a traves de la Data API de Supabase (deny-all).
--   * La autorizacion (admin / operador) vive en el backend FastAPI.
--   * FastAPI se conecta con un rol que ignora RLS (DATABASE_URL directa o
--     clave service_role). Ese secreto vive SOLO como variable de entorno en
--     Render: nunca en el frontend, el repositorio ni Vercel.
--   * El frontend usa unicamente la clave anon, y solo para el login de Supabase Auth.
--
-- Datos iniciales:
--   * Se cargan los roles. El primer usuario admin no se siembra aqui porque
--     usuario.id debe coincidir con un id existente en auth.users: se crea
--     primero en Supabase Auth y luego se inserta la fila en usuario.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- Usuarios y roles (modulos 1 y 10)
-- ---------------------------------------------------------------------
CREATE TABLE rol (
    id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre  TEXT NOT NULL UNIQUE
);

-- usuario.id es el MISMO UUID que auth.users.id (Supabase Auth).
-- No tiene DEFAULT: el backend crea primero el usuario en Supabase Auth
-- (Admin API) y luego inserta esta fila con el id devuelto.
CREATE TABLE usuario (
    id      UUID PRIMARY KEY REFERENCES auth.users(id),
    nombre  TEXT    NOT NULL,
    email   TEXT    NOT NULL UNIQUE,
    rol_id  UUID    NOT NULL REFERENCES rol(id),
    activo  BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- Propiedades y propietarios (modulo 2)
-- ---------------------------------------------------------------------
CREATE TABLE propiedad (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    direccion   TEXT NOT NULL,
    localidad   TEXT,
    estado      TEXT NOT NULL DEFAULT 'activa'
                CHECK (estado IN ('activa', 'inactiva')),
    fecha_alta  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE propietario (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre    TEXT NOT NULL,
    cuit_dni  TEXT,
    email     TEXT,
    estado    TEXT NOT NULL DEFAULT 'activa'
              CHECK (estado IN ('activa', 'inactiva')),
    telefono  TEXT
);

-- El % de reparto es vigente por propiedad y un propietario no se repite en la misma propiedad.
-- Que los porcentajes de una propiedad sumen 100 se valida en el backend, y los cambios
-- se aplican como UNA transaccion que reemplaza todas las filas de la propiedad y valida
-- la suma antes del COMMIT (nunca se pasa por estados intermedios invalidos).
-- Las preliquidaciones pasadas quedan protegidas por su propia copia en reparto.
-- Extension futura (no implementada): vigencia temporal por fila.
CREATE TABLE propiedad_propietario (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    propiedad_id   UUID NOT NULL REFERENCES propiedad(id),
    propietario_id UUID NOT NULL REFERENCES propietario(id),
    porcentaje     NUMERIC(5,2) NOT NULL
                   CHECK (porcentaje > 0 AND porcentaje <= 100),
    UNIQUE (propiedad_id, propietario_id)
);

-- ---------------------------------------------------------------------
-- Catalogo de conceptos y plantilla por propiedad (modulos 3 y 4)
-- ---------------------------------------------------------------------
-- umbral_variacion_pct: umbral propio del concepto para la advertencia de
-- variacion inusual. NULL = usar el umbral global por defecto (30.00, valor
-- inicial a confirmar con la inmobiliaria; se configura en el backend).
-- Umbral efectivo = COALESCE(concepto.umbral_variacion_pct, umbral global).
CREATE TABLE concepto (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre               TEXT NOT NULL UNIQUE,
    tipo                 TEXT,
    umbral_variacion_pct NUMERIC(5,2)
                         CHECK (umbral_variacion_pct > 0)
);

CREATE TABLE concepto_propiedad (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    propiedad_id UUID NOT NULL REFERENCES propiedad(id),
    concepto_id  UUID NOT NULL REFERENCES concepto(id),
    activo       BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (propiedad_id, concepto_id),
    -- Permite la FK compuesta de checklist_periodo (garantiza que el
    -- concepto_propiedad pertenece a la misma propiedad que el checklist).
    UNIQUE (id, propiedad_id)
);

-- ---------------------------------------------------------------------
-- Checklist persistido por periodo (modulo 5)
-- Al abrir un periodo para una propiedad, el backend inserta una fila por cada
-- concepto_propiedad ACTIVO con estado 'pendiente'.
--   * Cargar un importe -> 'cargado'.
--   * El usuario puede marcar 'no_corresponde'.
--   * Importe 0 es un valor cargado (estado 'cargado'); 'pendiente' y
--     'no_corresponde' son estados del checklist, no importes.
-- Generar una preliquidacion se BLOQUEA mientras haya filas 'pendiente', salvo
-- confirmacion explicita del usuario, que se registra como advertencia
-- de tipo 'pendiente_confirmado' en preliquidacion_advertencia.
-- ---------------------------------------------------------------------
CREATE TABLE checklist_periodo (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    propiedad_id          UUID NOT NULL REFERENCES propiedad(id),
    periodo               DATE NOT NULL,
    concepto_propiedad_id UUID NOT NULL,
    estado                TEXT NOT NULL DEFAULT 'pendiente'
                          CHECK (estado IN ('pendiente', 'cargado', 'no_corresponde')),
    CONSTRAINT ck_checklist_periodo_primer_dia
        CHECK (periodo = date_trunc('month', periodo::timestamp)::date),
    CONSTRAINT fk_checklist_concepto_propiedad
        FOREIGN KEY (concepto_propiedad_id, propiedad_id)
        REFERENCES concepto_propiedad (id, propiedad_id),
    UNIQUE (propiedad_id, periodo, concepto_propiedad_id)
);

-- ---------------------------------------------------------------------
-- Importes mensuales (modulo 6)
-- ---------------------------------------------------------------------
-- importe: SIN CHECK de signo a proposito. Se admiten importes negativos
-- (notas de credito, bonificaciones). El valor 0 es un importe valido.
CREATE TABLE importe_mensual (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concepto_propiedad_id UUID NOT NULL REFERENCES concepto_propiedad(id),
    periodo               DATE NOT NULL,
    importe               NUMERIC(14,2) NOT NULL,
    cargado_por           UUID NOT NULL REFERENCES usuario(id),
    fecha_carga           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_importe_periodo_primer_dia
        CHECK (periodo = date_trunc('month', periodo::timestamp)::date)
);

-- Un unico importe por concepto_propiedad y periodo (evita duplicados).
-- Tambien sirve como indice de busqueda por (concepto_propiedad_id, periodo).
CREATE UNIQUE INDEX uq_importe_concepto_periodo
    ON importe_mensual (concepto_propiedad_id, periodo);

-- ---------------------------------------------------------------------
-- Preliquidaciones, detalle, advertencias y reparto (modulos 7, 8 y 11)
-- Una preliquidacion es un resumen validado de conceptos variables y su
-- reparto entre propietarios. NO es la liquidacion oficial (la produce Maru).
--
-- Se persisten como SNAPSHOT INMUTABLE y VERSIONADO:
--   * Nunca se actualizan ni se borran (ver triggers mas abajo).
--   * Corregir un error = generar una nueva version (v2 reemplaza a v1,
--     ambas se conservan y v1 queda intacta).
--   * La version VIGENTE de una propiedad y un periodo es la de MAX(version);
--     ver la vista preliquidacion_vigente.
--   * Las FK hacia preliquidacion NO usan ON DELETE CASCADE (NO ACTION).
-- ---------------------------------------------------------------------
-- importe_total: SUM(preliquidacion_detalle.importe). Puede ser negativo.
CREATE TABLE preliquidacion (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    propiedad_id  UUID NOT NULL REFERENCES propiedad(id),
    periodo       DATE NOT NULL,
    version       INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    importe_total NUMERIC(14,2) NOT NULL,
    generado_por  UUID NOT NULL REFERENCES usuario(id),
    generado_en   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_preliquidacion_periodo_primer_dia
        CHECK (periodo = date_trunc('month', periodo::timestamp)::date),
    UNIQUE (propiedad_id, periodo, version)
);

-- Detalle inmutable: concepto y importe aplicado en esta version.
-- Incluye los conceptos en estado 'cargado' (importe 0 incluido).
CREATE TABLE preliquidacion_detalle (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    preliquidacion_id UUID NOT NULL REFERENCES preliquidacion(id),
    concepto_id      UUID NOT NULL REFERENCES concepto(id),
    importe          NUMERIC(14,2) NOT NULL,
    UNIQUE (preliquidacion_id, concepto_id)
);

-- tipo:
--   variacion_inusual     importe que supera el umbral respecto del periodo anterior (no bloqueante)
--   sin_referencia        nota informativa: sin periodo anterior, concepto nuevo o valor anterior 0
--   total_negativo        el importe_total de la preliquidacion es negativo
--   pendiente_confirmado  concepto 'pendiente' en el checklist que el usuario confirmo
--                         explicitamente generar sin cargar (una fila por concepto)
CREATE TABLE preliquidacion_advertencia (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    preliquidacion_id UUID NOT NULL REFERENCES preliquidacion(id),
    tipo              TEXT NOT NULL
                      CHECK (tipo IN ('variacion_inusual', 'sin_referencia',
                                      'total_negativo', 'pendiente_confirmado')),
    detalle           TEXT
);

-- Reparto propio de cada preliquidacion: porcentaje_aplicado se copia de
-- propiedad_propietario al generar la preliquidacion.
-- Redondeo: el importe de cada propietario se redondea a 2 decimales y el
-- ultimo propietario (mayor id, orden determinista) absorbe el resto de
-- centavos para que el reparto sume exactamente importe_total.
-- importe_correspondiente puede ser negativo (total negativo).
CREATE TABLE reparto (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    preliquidacion_id       UUID NOT NULL REFERENCES preliquidacion(id),
    propietario_id          UUID NOT NULL REFERENCES propietario(id),
    porcentaje_aplicado     NUMERIC(5,2)  NOT NULL
                            CHECK (porcentaje_aplicado > 0 AND porcentaje_aplicado <= 100),
    importe_correspondiente NUMERIC(14,2) NOT NULL,
    UNIQUE (preliquidacion_id, propietario_id)
);

-- Version vigente: la de mayor numero por (propiedad_id, periodo).
-- security_invoker = true: la vista respeta las restricciones (RLS) del rol que
-- consulta; sin esto, en Supabase una vista corre con los permisos de su duenio
-- y quedaria expuesta a la Data API pasando por encima de la RLS.
-- Requiere PostgreSQL 15+ (Supabase lo cumple).
CREATE VIEW preliquidacion_vigente
    WITH (security_invoker = true) AS
SELECT DISTINCT ON (propiedad_id, periodo)
       id, propiedad_id, periodo, version, importe_total, generado_por, generado_en
FROM preliquidacion
ORDER BY propiedad_id, periodo, version DESC;

-- ---------------------------------------------------------------------
-- Inmutabilidad de los snapshots (trigger de resguardo)
-- Bloquea UPDATE, DELETE y TRUNCATE sobre las tablas del snapshot. Protege
-- contra errores de la aplicacion; un superusuario podria deshabilitar el
-- trigger a proposito. Corregir = insertar una nueva version, nunca modificar.
-- ---------------------------------------------------------------------
CREATE FUNCTION bloquear_modificacion_snapshot() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'La tabla % es inmutable: no se permite % (para corregir, generar una nueva version)',
        TG_TABLE_NAME, TG_OP
        USING ERRCODE = 'restrict_violation';
END;
$$;

CREATE TRIGGER tg_preliquidacion_inmutable
    BEFORE UPDATE OR DELETE ON preliquidacion
    FOR EACH ROW EXECUTE FUNCTION bloquear_modificacion_snapshot();
CREATE TRIGGER tg_preliquidacion_sin_truncate
    BEFORE TRUNCATE ON preliquidacion
    FOR EACH STATEMENT EXECUTE FUNCTION bloquear_modificacion_snapshot();

CREATE TRIGGER tg_preliquidacion_detalle_inmutable
    BEFORE UPDATE OR DELETE ON preliquidacion_detalle
    FOR EACH ROW EXECUTE FUNCTION bloquear_modificacion_snapshot();
CREATE TRIGGER tg_preliquidacion_detalle_sin_truncate
    BEFORE TRUNCATE ON preliquidacion_detalle
    FOR EACH STATEMENT EXECUTE FUNCTION bloquear_modificacion_snapshot();

CREATE TRIGGER tg_preliquidacion_advertencia_inmutable
    BEFORE UPDATE OR DELETE ON preliquidacion_advertencia
    FOR EACH ROW EXECUTE FUNCTION bloquear_modificacion_snapshot();
CREATE TRIGGER tg_preliquidacion_advertencia_sin_truncate
    BEFORE TRUNCATE ON preliquidacion_advertencia
    FOR EACH STATEMENT EXECUTE FUNCTION bloquear_modificacion_snapshot();

CREATE TRIGGER tg_reparto_inmutable
    BEFORE UPDATE OR DELETE ON reparto
    FOR EACH ROW EXECUTE FUNCTION bloquear_modificacion_snapshot();
CREATE TRIGGER tg_reparto_sin_truncate
    BEFORE TRUNCATE ON reparto
    FOR EACH STATEMENT EXECUTE FUNCTION bloquear_modificacion_snapshot();

-- ---------------------------------------------------------------------
-- Auditoria (modulo 9)
-- entidad + entidad_id permiten registrar acciones sobre cualquier tabla
-- ---------------------------------------------------------------------
CREATE TABLE auditoria (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id  UUID NOT NULL REFERENCES usuario(id),
    accion      TEXT NOT NULL,
    entidad     TEXT NOT NULL,
    entidad_id  UUID,
    detalle     JSONB,
    fecha       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_auditoria_entidad ON auditoria (entidad, entidad_id);
CREATE INDEX idx_auditoria_fecha   ON auditoria (fecha);

-- ---------------------------------------------------------------------
-- Datos iniciales
-- ---------------------------------------------------------------------
INSERT INTO rol (nombre) VALUES ('admin'), ('operador');

-- ---------------------------------------------------------------------
-- Row Level Security: activada en todas las tablas, SIN policies (deny-all
-- para anon/authenticated). Ver el encabezado de este archivo.
-- ---------------------------------------------------------------------
ALTER TABLE rol                        ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuario                    ENABLE ROW LEVEL SECURITY;
ALTER TABLE propiedad                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE propietario                ENABLE ROW LEVEL SECURITY;
ALTER TABLE propiedad_propietario      ENABLE ROW LEVEL SECURITY;
ALTER TABLE concepto                   ENABLE ROW LEVEL SECURITY;
ALTER TABLE concepto_propiedad         ENABLE ROW LEVEL SECURITY;
ALTER TABLE checklist_periodo          ENABLE ROW LEVEL SECURITY;
ALTER TABLE importe_mensual            ENABLE ROW LEVEL SECURITY;
ALTER TABLE preliquidacion             ENABLE ROW LEVEL SECURITY;
ALTER TABLE preliquidacion_detalle     ENABLE ROW LEVEL SECURITY;
ALTER TABLE preliquidacion_advertencia ENABLE ROW LEVEL SECURITY;
ALTER TABLE reparto                    ENABLE ROW LEVEL SECURITY;
ALTER TABLE auditoria                  ENABLE ROW LEVEL SECURITY;

COMMIT;
