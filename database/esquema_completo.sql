-- =====================================================================
-- Sistema de asistencia para liquidación de alquileres
-- Script de creación de base de datos (PostgreSQL / Supabase)
-- =====================================================================
-- Convenciones:
--   * ids UUID generados con gen_random_uuid() (disponible en PostgreSQL 13+ y Supabase)
--   * periodo (DATE): se guarda el primer día del mes (ej. 2026-09-01)
--   * importes NUMERIC(14,2); porcentajes NUMERIC(5,2)
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- Usuarios y roles (módulos 1 y 9)
-- ---------------------------------------------------------------------
CREATE TABLE rol (
    id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre  TEXT NOT NULL UNIQUE
);

-- Si se quiere que usuario.id coincida con el id de Supabase Auth, se puede
-- quitar el DEFAULT y agregar: REFERENCES auth.users(id)
CREATE TABLE usuario (
    id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre  TEXT    NOT NULL,
    email   TEXT    NOT NULL UNIQUE,
    rol_id  UUID    NOT NULL REFERENCES rol(id),
    activo  BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- Propiedades y propietarios (módulo 2)
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

-- El % de reparto es fijo por propiedad.
-- Que los porcentajes de una propiedad sumen 100 se valida en el backend.
CREATE TABLE propiedad_propietario (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    propiedad_id   UUID NOT NULL REFERENCES propiedad(id),
    propietario_id UUID NOT NULL REFERENCES propietario(id),
    porcentaje     NUMERIC(5,2) NOT NULL
                   CHECK (porcentaje > 0 AND porcentaje <= 100),
    UNIQUE (propiedad_id, propietario_id)
);

-- ---------------------------------------------------------------------
-- Catálogo de conceptos y plantilla por propiedad (módulos 3 y 4)
-- ---------------------------------------------------------------------
CREATE TABLE concepto (
    id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre  TEXT NOT NULL UNIQUE,
    tipo    TEXT
);

CREATE TABLE concepto_propiedad (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    propiedad_id UUID NOT NULL REFERENCES propiedad(id),
    concepto_id  UUID NOT NULL REFERENCES concepto(id),
    activo       BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (propiedad_id, concepto_id)
);

-- ---------------------------------------------------------------------
-- Importes mensuales (módulo 5)
-- ---------------------------------------------------------------------
CREATE TABLE importe_mensual (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concepto_propiedad_id UUID NOT NULL REFERENCES concepto_propiedad(id),
    periodo               DATE NOT NULL,
    importe               NUMERIC(14,2) NOT NULL,
    cargado_por           UUID NOT NULL REFERENCES usuario(id),
    fecha_carga           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_importe_concepto_periodo
    ON importe_mensual (concepto_propiedad_id, periodo);

CREATE UNIQUE INDEX uq_importe_concepto_periodo
ON importe_mensual (concepto_propiedad_id, periodo);

-- ---------------------------------------------------------------------
-- Liquidaciones, advertencias y reparto (módulos 6, 7 y 10)
-- Las liquidaciones se persisten como snapshot.
-- ---------------------------------------------------------------------
CREATE TABLE liquidacion (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    propiedad_id  UUID NOT NULL REFERENCES propiedad(id),
    periodo       DATE NOT NULL,
    importe_total NUMERIC(14,2) NOT NULL,
    generado_por  UUID NOT NULL REFERENCES usuario(id),
    generado_en   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_liquidacion_propiedad_periodo
    ON liquidacion (propiedad_id, periodo);

-- tipo: variación inusual de importe o concepto activo sin cargar
CREATE TABLE liquidacion_advertencia (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    liquidacion_id UUID NOT NULL REFERENCES liquidacion(id) ON DELETE CASCADE,
    tipo           TEXT NOT NULL,
    detalle        TEXT
);

CREATE TABLE reparto (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    liquidacion_id          UUID NOT NULL REFERENCES liquidacion(id) ON DELETE CASCADE,
    propietario_id          UUID NOT NULL REFERENCES propietario(id),
    porcentaje_aplicado     NUMERIC(5,2)  NOT NULL
                            CHECK (porcentaje_aplicado > 0 AND porcentaje_aplicado <= 100),
    importe_correspondiente NUMERIC(14,2) NOT NULL
);

-- ---------------------------------------------------------------------
-- Auditoría (módulo 8)
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
-- Contratos e inquilinos (módulo 11)
-- ---------------------------------------------------------------------
CREATE TABLE inquilino (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dni       TEXT NOT NULL UNIQUE,
    nombre    TEXT NOT NULL,
    apellido  TEXT NOT NULL,
    telefono  TEXT,
    email     TEXT,
    estado    TEXT NOT NULL DEFAULT 'activo'
              CHECK (estado IN ('activo', 'inactivo'))
);

-- Los contratos no se pisan: al renovar se crea uno nuevo y el anterior pasa a 'renovado'.
CREATE TABLE contrato (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    propiedad_id          UUID NOT NULL REFERENCES propiedad(id),
    fecha_inicio          DATE NOT NULL,
    fecha_fin             DATE NOT NULL,
    estado                TEXT NOT NULL DEFAULT 'vigente'
                          CHECK (estado IN ('vigente', 'vencido', 'renovado', 'rescindido')),
    contrato_anterior_id  UUID REFERENCES contrato(id),
    fecha_alta            TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (fecha_fin > fecha_inicio)
);

-- Acelera la búsqueda diaria de contratos vigentes próximos a vencer
CREATE INDEX idx_contrato_vigente_fecha_fin
    ON contrato (fecha_fin) WHERE estado = 'vigente';

CREATE INDEX idx_contrato_propiedad ON contrato (propiedad_id);

CREATE UNIQUE INDEX uq_contrato_vigente_por_propiedad
ON contrato (propiedad_id) WHERE estado = 'vigente';

CREATE TABLE contrato_inquilino (
    contrato_id  UUID NOT NULL REFERENCES contrato(id),
    inquilino_id UUID NOT NULL REFERENCES inquilino(id),
    PRIMARY KEY (contrato_id, inquilino_id)
);

-- ---------------------------------------------------------------------
-- Alertas de vencimiento de contratos (módulo 12)
-- UNIQUE (contrato_id, tipo) evita duplicar la alerta aunque el proceso diario
-- falle un día o se ejecute más de una vez.
-- email_enviado_en NULL = email todavía no enviado.
-- ---------------------------------------------------------------------
CREATE TABLE alerta_vencimiento (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contrato_id       UUID NOT NULL REFERENCES contrato(id),
    tipo              TEXT NOT NULL CHECK (tipo IN ('20_dias', '7_dias')),
    fecha_generacion  DATE NOT NULL DEFAULT CURRENT_DATE,
    estado            TEXT NOT NULL DEFAULT 'pendiente'
                      CHECK (estado IN ('pendiente', 'en_gestion', 'resuelta')),
    email_enviado_en  TIMESTAMPTZ,
    UNIQUE (contrato_id, tipo)
);

-- ---------------------------------------------------------------------
-- Datos iniciales
-- ---------------------------------------------------------------------
INSERT INTO rol (nombre) VALUES ('admin'), ('operador');

-- ---------------------------------------------------------------------
ALTER TABLE rol                     ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuario                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE propiedad               ENABLE ROW LEVEL SECURITY;
ALTER TABLE propietario             ENABLE ROW LEVEL SECURITY;
ALTER TABLE propiedad_propietario   ENABLE ROW LEVEL SECURITY;
ALTER TABLE concepto                ENABLE ROW LEVEL SECURITY;
ALTER TABLE concepto_propiedad      ENABLE ROW LEVEL SECURITY;
ALTER TABLE importe_mensual         ENABLE ROW LEVEL SECURITY;
ALTER TABLE liquidacion             ENABLE ROW LEVEL SECURITY;
ALTER TABLE liquidacion_advertencia ENABLE ROW LEVEL SECURITY;
ALTER TABLE reparto                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE auditoria               ENABLE ROW LEVEL SECURITY;
ALTER TABLE inquilino               ENABLE ROW LEVEL SECURITY;
ALTER TABLE contrato                ENABLE ROW LEVEL SECURITY;
ALTER TABLE contrato_inquilino      ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerta_vencimiento      ENABLE ROW LEVEL SECURITY;

COMMIT;
