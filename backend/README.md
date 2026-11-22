# Backend

API REST del sistema de preliquidación de alquileres. Está hecha con FastAPI y PostgreSQL (Supabase), y la consume el frontend de este repositorio.

## Tecnologías

| Para qué | Qué usamos |
|---|---|
| Framework web | FastAPI + Uvicorn |
| Acceso a la base de datos | SQLModel (SQLAlchemy) con `psycopg` |
| Configuración | `pydantic-settings` (lee variables de entorno) |
| Validación del token de sesión | PyJWT |
| Pruebas | pytest + httpx |
| Base de datos y Auth | PostgreSQL en Supabase |

## Requisitos

- Python 3.13.
- PostgreSQL local, solo para correr las pruebas.
- Un proyecto de Supabase, solo si querés levantar el sistema completo. Los pasos de la base de datos están en el [README de la raíz](../README.md#ejecución-en-local).

## Ejecución en local

Desde la carpeta `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # completar los valores (ver la sección siguiente)
uvicorn app.main:app --reload
```

El servidor queda en `http://localhost:8000`.

- `http://localhost:8000/health` informa el estado del servicio y de la base de datos.
- `http://localhost:8000/docs` muestra la documentación interactiva de la API (Swagger), donde se pueden probar los endpoints. Para los que piden sesión, hay que enviar un token de Supabase.

## Variables de entorno

Se leen desde `backend/.env`. Ese archivo no se sube al repositorio. Lo que se sube es `.env.example`, que sirve de modelo.

| Variable | Qué es |
|---|---|
| `DATABASE_URL` | Conexión a PostgreSQL |
| `SUPABASE_URL` | URL del proyecto de Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Clave de servicio de Supabase (se usa para crear usuarios). **Es secreta** |
| `SUPABASE_JWT_SECRET` | Secreto para validar el token de sesión en cada pedido. **Es secreto** |
| `CORS_ALLOWED_ORIGIN` | Único origen del frontend que puede llamar a la API. En local: `http://localhost:5173` |
| `UMBRAL_VARIACION_DEFAULT_PCT` | Umbral global de variación inusual, en porcentaje (por defecto `30.00`) |
| `TEST_DATABASE_URL` | Base descartable para las pruebas (ver más abajo) |

Nunca subas el `.env` ni pegues estas claves en el README, en issues o en PR.

## Estructura

```text
backend/
├── app/
│   ├── main.py          # Crea la aplicación y registra los módulos
│   ├── core/            # Piezas compartidas por todos los módulos
│   │   ├── config.py    # Lectura de las variables de entorno
│   │   ├── db.py        # Conexión a la base de datos
│   │   ├── security.py  # Validación del token de sesión
│   │   ├── deps.py      # Usuario actual y control de permisos
│   │   ├── errors.py    # Formato único de errores
│   │   ├── contract.py  # Respuestas de error que se declaran en el contrato
│   │   └── me.py        # Datos del usuario que inició sesión
│   ├── audit/           # Registro de quién hizo cada operación y cuándo
│   └── modules/         # Un directorio por módulo del sistema
├── scripts/
│   └── generar_openapi.py   # Genera docs/openapi.json
├── tests/
├── pytest.ini
└── requirements.txt
```

### Módulos (`app/modules/`)

`propiedades`, `usuarios`, `conceptos`, `plantilla`, `reparto`, `checklist`, `importes`, `advertencias` y `preliquidaciones`.

Cada módulo se organiza en capas, para que cada archivo tenga una sola responsabilidad. Por ejemplo, `propiedades/` tiene:

| Archivo | Qué hace |
|---|---|
| `router.py` | Define las rutas HTTP y recibe los pedidos |
| `schemas.py` | Describe la forma de los datos que entran y salen |
| `service.py` | Contiene las reglas de negocio |
| `repository.py` | Hace las consultas a la base de datos |
| `models.py` | Define las tablas como clases de Python |

## Autenticación y permisos

1. El usuario inicia sesión en el frontend con Supabase Auth, que le entrega un token.
2. El frontend envía ese token en cada pedido, en el encabezado `Authorization: Bearer <token>`.
3. El backend verifica la firma, la expiración y la audiencia del token (`core/security.py`).
4. Luego busca al usuario en la tabla `usuario`. Si no está registrado o está inactivo, rechaza el pedido (`core/deps.py`).

Todas las rutas de los módulos exigen sesión iniciada. La única ruta pública es `/health`.

Hay dos roles: `operador`, que puede usar el sistema completo salvo la gestión de usuarios, y `admin`, que además gestiona usuarios. Los endpoints exclusivos del administrador usan la dependencia `require_admin`.

## Formato de errores

Todos los errores tienen la misma forma, para que el frontend pueda mostrarlos siempre igual:

```json
{
  "codigo": "no_autenticado",
  "mensaje": "Falta el token de autenticación",
  "detalle": {}
}
```

| Estado | Cuándo ocurre |
|---|---|
| 401 | Falta el token, es inválido o expiró |
| 403 | Usuario no registrado, inactivo o sin el rol necesario |
| 404 | El recurso no existe |
| 409 | Conflicto, por ejemplo un dato duplicado |
| 422 | Datos de entrada inválidos. El `detalle` lista los campos con error |
| 500 | Error interno. Se registra en el log del servidor |

Para lanzar un error propio desde el código se usa `AppError(status, codigo, mensaje, detalle)`, definido en `core/errors.py`.

## Pruebas

Las pruebas recrean el esquema de la base en cada corrida, por eso usan una **base PostgreSQL local y descartable**, nunca la real. Si el host de `TEST_DATABASE_URL` no es local o el nombre de la base no termina en `_test`, pytest se detiene para no tocar datos reales.

```bash
# 1. Crear la base de pruebas (una sola vez)
createdb preliquidacion_test

# 2. En backend/.env, apuntar TEST_DATABASE_URL a esa base
#    (usuario y contraseña según tu instalación de PostgreSQL)
# TEST_DATABASE_URL=postgresql://usuario:clave@localhost:5432/preliquidacion_test

# 3. Correr las pruebas desde backend/
python -m pytest
```

Resultado esperado: `338 passed`.

Para correr solo una parte:

```bash
python -m pytest tests/propiedades          # un módulo
python -m pytest tests/test_auth.py -v      # un archivo, con detalle
```

Qué cubre cada grupo:

- `tests/<módulo>/`: pruebas de cada módulo.
- `tests/cross/`: pruebas que recorren varios módulos juntos (Gate 1).
- `test_auth.py`, `test_rutas_protegidas.py`, `test_rls_anon.py`: sesión, permisos y seguridad de la base.
- `test_contrato.py`: que la API coincida con `docs/openapi.json`.
- `test_esquema.py`, `test_audit.py`, `test_health.py`: esquema, auditoría y estado del servicio.

## Contrato de la API (OpenAPI)

El contrato de la API vive en `docs/openapi.json` y se genera a partir del código. Si cambiás rutas, datos de entrada o de salida, hay que regenerarlo y también los tipos del frontend:

```bash
# Desde backend/
python -m scripts.generar_openapi        # actualiza docs/openapi.json

# Desde frontend/
npm run gen:api                          # actualiza src/types/api.ts
```

Después de regenerar, subí los dos archivos en el mismo PR. El CI falla si quedan desactualizados.

## Despliegue

El backend corre en Render. Las variables de entorno se cargan en el panel de Render, no en un archivo. Dos cosas para tener en cuenta:

- `CORS_ALLOWED_ORIGIN` tiene que ser la URL de producción del frontend en Vercel. Acepta un solo origen.
- Render duerme el servicio cuando no tiene tráfico, y el primer pedido puede tardar cerca de un minuto. Abrir `/health` antes de usar el sistema lo despierta.

Las URLs del sistema desplegado y el resto de la documentación están en el [README de la raíz](../README.md).