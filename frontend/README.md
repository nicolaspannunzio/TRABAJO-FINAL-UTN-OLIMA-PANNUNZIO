# Frontend

Interfaz web del sistema de liquidación de expensas. Es una aplicación de una sola página (SPA) hecha con React y TypeScript, que consume la API del backend.

## Tecnologías

| Para qué | Qué usamos |
|---|---|
| Interfaz | React 19 + TypeScript |
| Empaquetado y servidor de desarrollo | Vite |
| Rutas | TanStack Router (rutas por archivos) |
| Datos del servidor (consultas y caché) | TanStack Query |
| Formularios | TanStack Form |
| Tablas | TanStack Table |
| Inicio de sesión | Supabase Auth (`@supabase/supabase-js`) |
| Calidad de código | ESLint + `tsc` |

## Requisitos

- Node.js 20.19 o superior (lo que pide Vite) y npm.
- El backend corriendo, ya sea en local o el desplegado. Ver el README de la raíz.

## Ejecución en local

Desde la carpeta `frontend/`:

```bash
# 1. Instalar dependencias
npm install

# 2. Crear el archivo de variables de entorno
cp .env.example .env
# Completar los valores (ver la sección siguiente)

# 3. Levantar el servidor de desarrollo
npm run dev
```

La aplicación queda disponible en la dirección que muestra Vite en la terminal (por defecto, `http://localhost:5173`).

> El backend solo acepta pedidos desde el origen configurado en su variable `CORS_ALLOWED_ORIGIN`. Si corrés el backend en local, esa variable tiene que apuntar a la dirección donde corre el frontend.

## Variables de entorno

Se leen desde `frontend/.env`. Ese archivo no se sube al repositorio. Lo que se sube es `.env.example`, que sirve de modelo.

| Variable | Qué es | Ejemplo |
|---|---|---|
| `VITE_API_URL` | URL base del backend, **sin barra final** | `http://localhost:8000` |
| `VITE_SUPABASE_URL` | URL del proyecto de Supabase | la entrega el equipo |
| `VITE_SUPABASE_ANON_KEY` | Clave pública (anon) de Supabase | la entrega el equipo |

Vite solo expone al navegador las variables que empiezan con `VITE_`. Por eso nunca hay que poner acá claves secretas: todo lo que esté en estas variables queda visible para quien abra la aplicación.

## Scripts

| Comando | Qué hace |
|---|---|
| `npm run dev` | Servidor de desarrollo con recarga automática |
| `npm run build` | Revisa los tipos con `tsc` y genera la versión de producción en `dist/` |
| `npm run preview` | Sirve localmente el resultado de `build` para probarlo |
| `npm run lint` | Corre ESLint sobre todo el proyecto |
| `npm run gen:api` | Regenera `src/types/api.ts` a partir de `docs/openapi.json` |

El CI de GitHub Actions corre los tipos, el build y el lint en cada PR. Conviene correr `npm run lint` y `npm run build` antes de abrir uno.

## Estructura

```text
frontend/
├── src/
│   ├── main.tsx            # Punto de entrada
│   ├── app/                # Configuración general
│   │   ├── App.tsx
│   │   ├── router.ts       # Creación del router
│   │   ├── queryClient.ts  # Configuración de TanStack Query
│   │   ├── navegacion.ts   # Entradas del menú
│   │   ├── routeTree.gen.ts  # GENERADO, no editar a mano
│   │   └── routes/         # Una pantalla por archivo
│   ├── features/           # Un directorio por módulo del sistema
│   ├── components/         # Piezas compartidas (Layout, Cargando, PantallaVacia)
│   ├── context/            # Sesión del usuario (SessionProvider)
│   ├── services/           # Acceso a la API (api.ts) y a Supabase (supabase.ts)
│   └── types/              # Tipos; api.ts se genera desde el contrato OpenAPI
├── public/
├── vercel.json             # Configuración de despliegue
└── vite.config.ts
```

### Pantallas (`src/app/routes/`)

- `login.tsx`: inicio de sesión (es la única pantalla pública).
- `_autenticado/`: todo lo que requiere sesión iniciada: `index`, `propiedades`, `conceptos`, `checklist`, `preliquidaciones` y `usuarios`.

El menú de navegación se define en `src/app/navegacion.ts`. Si se agrega una pantalla nueva, hay que sumarla