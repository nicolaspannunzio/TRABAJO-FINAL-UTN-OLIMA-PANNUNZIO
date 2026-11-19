# Diagrama entidad-relación (modelo corregido)

Entidades persistidas en PostgreSQL (Supabase). `AUTH_USERS` pertenece a Supabase Auth (esquema `auth`) y se muestra solo para indicar que `USUARIO.id` es el mismo UUID. Las reglas que el diagrama no expresa están en [`arquitectura.md`](arquitectura.md) (sección 4.5) y en [`../database/esquema_completo.sql`](../database/esquema_completo.sql).

```mermaid
erDiagram
    AUTH_USERS ||--|| USUARIO : mismo_id
    ROL ||--o{ USUARIO : asigna
    USUARIO ||--o{ AUDITORIA : registra_accion
    USUARIO ||--o{ IMPORTE_MENSUAL : carga
    USUARIO ||--o{ PRELIQUIDACION : genera_por

    PROPIEDAD ||--o{ PROPIEDAD_PROPIETARIO : tiene
    PROPIETARIO ||--o{ PROPIEDAD_PROPIETARIO : posee

    PROPIEDAD ||--o{ CONCEPTO_PROPIEDAD : aplica
    CONCEPTO ||--o{ CONCEPTO_PROPIEDAD : incluido_en

    PROPIEDAD ||--o{ CHECKLIST_PERIODO : abre_periodo
    CONCEPTO_PROPIEDAD ||--o{ CHECKLIST_PERIODO : esperado_en

    CONCEPTO_PROPIEDAD ||--o{ IMPORTE_MENSUAL : registra

    PROPIEDAD ||--o{ PRELIQUIDACION : genera
    PRELIQUIDACION ||--o{ PRELIQUIDACION_DETALLE : detalla
    CONCEPTO ||--o{ PRELIQUIDACION_DETALLE : aplicado_en
    PRELIQUIDACION ||--o{ PRELIQUIDACION_ADVERTENCIA : presenta
    PRELIQUIDACION ||--o{ REPARTO : distribuye
    PROPIETARIO ||--o{ REPARTO : recibe

    AUTH_USERS {
        uuid id PK
    }

    ROL {
        uuid id PK
        text nombre UK
    }

    USUARIO {
        uuid id PK "igual a auth.users.id"
        text nombre
        text email UK
        uuid rol_id FK
        boolean activo
    }

    PROPIEDAD {
        uuid id PK
        text direccion
        text localidad
        text estado
        timestamp fecha_alta
    }

    PROPIETARIO {
        uuid id PK
        text nombre
        text cuit_dni
        text email
        text estado
        text telefono
    }

    PROPIEDAD_PROPIETARIO {
        uuid id PK
        uuid propiedad_id FK
        uuid propietario_id FK
        numeric porcentaje
    }

    CONCEPTO {
        uuid id PK
        text nombre UK
        text tipo
        numeric umbral_variacion_pct "NULL usa el umbral global"
    }

    CONCEPTO_PROPIEDAD {
        uuid id PK
        uuid propiedad_id FK
        uuid concepto_id FK
        boolean activo
    }

    CHECKLIST_PERIODO {
        uuid id PK
        uuid propiedad_id FK
        date periodo "primer dia del mes"
        uuid concepto_propiedad_id FK
        text estado "pendiente, cargado, no_corresponde"
    }

    IMPORTE_MENSUAL {
        uuid id PK
        uuid concepto_propiedad_id FK
        date periodo "primer dia del mes"
        numeric importe "admite negativos"
        uuid cargado_por FK
        timestamp fecha_carga
    }

    PRELIQUIDACION {
        uuid id PK
        uuid propiedad_id FK
        date periodo "primer dia del mes"
        int version "UK con propiedad_id y periodo"
        numeric importe_total "admite negativos"
        uuid generado_por FK
        timestamp generado_en
    }

    PRELIQUIDACION_DETALLE {
        uuid id PK
        uuid preliquidacion_id FK
        uuid concepto_id FK
        numeric importe
    }

    PRELIQUIDACION_ADVERTENCIA {
        uuid id PK
        uuid preliquidacion_id FK
        text tipo
        text detalle
    }

    REPARTO {
        uuid id PK
        uuid preliquidacion_id FK
        uuid propietario_id FK
        numeric porcentaje_aplicado
        numeric importe_correspondiente
    }

    AUDITORIA {
        uuid id PK
        uuid usuario_id FK
        text accion
        text entidad
        uuid entidad_id
        jsonb detalle
        timestamp fecha
    }
```

## Restricciones que el diagrama no muestra

| Tabla | Restricción |
|---|---|
| `propiedad_propietario` | `UNIQUE (propiedad_id, propietario_id)` |
| `concepto_propiedad` | `UNIQUE (propiedad_id, concepto_id)` |
| `checklist_periodo` | `UNIQUE (propiedad_id, periodo, concepto_propiedad_id)`; FK compuesta `(concepto_propiedad_id, propiedad_id)` hacia `concepto_propiedad` |
| `importe_mensual` | `UNIQUE (concepto_propiedad_id, periodo)` |
| `preliquidacion` | `UNIQUE (propiedad_id, periodo, version)`, `version >= 1` |
| `preliquidacion_detalle` | `UNIQUE (preliquidacion_id, concepto_id)` |
| `reparto` | `UNIQUE (preliquidacion_id, propietario_id)` |
| `checklist_periodo`, `importe_mensual`, `preliquidacion` | `periodo` es el primer día del mes (`CHECK`) |
| `preliquidacion`, `preliquidacion_detalle`, `preliquidacion_advertencia`, `reparto` | Snapshot inmutable: trigger que rechaza `UPDATE`, `DELETE` y `TRUNCATE`; sin `ON DELETE CASCADE` |
| `concepto` | `UNIQUE INDEX uq_concepto_nombre_ci ON concepto (lower(nombre))` |

La vista `preliquidacion_vigente` devuelve, por `(propiedad_id, periodo)`, la fila de `preliquidacion` con mayor `version`.
