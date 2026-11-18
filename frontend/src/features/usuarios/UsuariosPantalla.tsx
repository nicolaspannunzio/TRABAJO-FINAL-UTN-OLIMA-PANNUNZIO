import { useMemo, useState } from 'react'
import { useForm } from '@tanstack/react-form'
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from '@tanstack/react-table'
import { Cargando } from '../../components/Cargando'
import { ApiError } from '../../services/api'
import { useActualizarUsuario, useCrearUsuario, useDarDeBaja, useUsuarios } from './queries'
import type { Rol, UsuarioOut } from './tipos'

// --- Textos de la interfaz ---------------------------------------------------

const ETIQUETA_ROL: Record<Rol, string> = {
  admin: 'Administrador',
  operador: 'Operador',
}

const ROLES: Rol[] = ['operador', 'admin']
const REGEX_EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

// El texto se elige según `codigo`, nunca según el mensaje del backend.
function textoError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.codigo) {
      case 'permiso_insuficiente':
        return 'Solo los administradores pueden gestionar usuarios.'
      case 'email_duplicado':
        return 'Ya existe un usuario con ese email.'
      case 'contrasena_invalida':
        return 'La contraseña no cumple los requisitos. Probá con una más larga.'
      case 'usuario_no_encontrado':
        return 'El usuario ya no existe. Se actualizó la lista.'
      case 'validacion':
        return 'Revisá los datos: algún campo no es válido.'
      case 'auth_error':
        return 'No se pudo crear la cuenta en el servicio de autenticación. No se creó nada; probá de nuevo.'
      case 'error_interno':
        return 'Ocurrió un error en el servidor. No se creó el usuario.'
      case 'sin_conexion':
        return 'No se pudo conectar con el servidor. Si recién arranca, probá de nuevo en unos segundos.'
    }
  }
  return 'Ocurrió un error inesperado.'
}

function MensajeError({ error }: { error: unknown }) {
  return (
    <p role="alert" style={{ color: 'crimson' }}>
      {textoError(error)}
    </p>
  )
}

function ErrorDeCampo({ errores }: { errores: unknown[] }) {
  if (errores.length === 0) return null
  return (
    <span role="alert" style={{ display: 'block', color: 'crimson' }}>
      {errores.map(String).join(', ')}
    </span>
  )
}

// --- Pantalla ----------------------------------------------------------------

export function UsuariosPantalla() {
  const usuarios = useUsuarios()
  const [editando, setEditando] = useState<UsuarioOut | null>(null)

  if (usuarios.isPending) return <Cargando />
  if (usuarios.isError) return <MensajeError error={usuarios.error} />

  return (
    <section>
      <h1>Usuarios</h1>

      <FormularioAlta />

      <h2 style={{ marginTop: '2rem' }}>Usuarios del sistema</h2>
      {usuarios.data.length === 0 ? (
        <p>Todavía no hay usuarios.</p>
      ) : (
        <TablaUsuarios usuarios={usuarios.data} onEditar={setEditando} />
      )}

      {editando && (
        <FormularioEdicion
          key={editando.id}
          usuario={editando}
          onTerminar={() => setEditando(null)}
        />
      )}
    </section>
  )
}

// --- Alta (HU-02) ------------------------------------------------------------

function FormularioAlta() {
  const crear = useCrearUsuario()
  const [creado, setCreado] = useState<string | null>(null)

  const form = useForm({
    defaultValues: { email: '', nombre: '', rol: 'operador' as Rol, contrasena: '' },
    onSubmit: async ({ value, formApi }) => {
      setCreado(null)
      try {
        const usuario = await crear.mutateAsync(value)
        setCreado(usuario.email)
        formApi.reset()
      } catch {
        // el error queda en crear.error y se muestra abajo; el formulario conserva lo escrito
      }
    },
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        e.stopPropagation()
        void form.handleSubmit()
      }}
      style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start', flexWrap: 'wrap' }}
    >
      <form.Field
        name="email"
        validators={{
          onSubmit: ({ value }) => (REGEX_EMAIL.test(value) ? undefined : 'Ingresá un email válido'),
        }}
      >
        {(field) => (
          <label>
            Email
            <br />
            <input
              type="email"
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              onBlur={field.handleBlur}
            />
            <ErrorDeCampo errores={field.state.meta.errors} />
          </label>
        )}
      </form.Field>

      <form.Field
        name="nombre"
        validators={{
          onSubmit: ({ value }) => (value.trim() ? undefined : 'Ingresá el nombre'),
        }}
      >
        {(field) => (
          <label>
            Nombre
            <br />
            <input
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              onBlur={field.handleBlur}
            />
            <ErrorDeCampo errores={field.state.meta.errors} />
          </label>
        )}
      </form.Field>

      <form.Field name="rol">
        {(field) => (
          <label>
            Rol
            <br />
            <select
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value as Rol)}
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {ETIQUETA_ROL[r]}
                </option>
              ))}
            </select>
          </label>
        )}
      </form.Field>

      <form.Field
        name="contrasena"
        validators={{
          onSubmit: ({ value }) => (value.length >= 6 ? undefined : 'Mínimo 6 caracteres'),
        }}
      >
        {(field) => (
          <label>
            Contraseña inicial
            <br />
            <input
              type="password"
              autoComplete="new-password"
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              onBlur={field.handleBlur}
            />
            <ErrorDeCampo errores={field.state.meta.errors} />
          </label>
        )}
      </form.Field>

      <div style={{ alignSelf: 'flex-end' }}>
        <button type="submit" disabled={crear.isPending}>
          {crear.isPending ? 'Creando…' : 'Crear usuario'}
        </button>
      </div>

      <div style={{ flexBasis: '100%' }}>
        <small>
          La contraseña inicial la define el administrador. No se pide cambiarla en el primer
          ingreso: pasásela a la persona por un canal seguro.
        </small>
        {crear.isError && <MensajeError error={crear.error} />}
        {creado && <p role="status">Usuario {creado} creado.</p>}
      </div>
    </form>
  )
}

// --- Edición -----------------------------------------------------------------

function FormularioEdicion({ usuario, onTerminar }: { usuario: UsuarioOut; onTerminar: () => void }) {
  const actualizar = useActualizarUsuario()

  const form = useForm({
    defaultValues: { nombre: usuario.nombre, rol: usuario.rol },
    onSubmit: async ({ value }) => {
      try {
        await actualizar.mutateAsync({ id: usuario.id, datos: value })
        onTerminar()
      } catch {
        // el error queda en actualizar.error y se muestra abajo
      }
    },
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        e.stopPropagation()
        void form.handleSubmit()
      }}
      style={{ marginTop: '2rem' }}
    >
      <h2>Editar {usuario.email}</h2>
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start', flexWrap: 'wrap' }}>
        <form.Field
          name="nombre"
          validators={{
            onSubmit: ({ value }) => (value.trim() ? undefined : 'Ingresá el nombre'),
          }}
        >
          {(field) => (
            <label>
              Nombre
              <br />
              <input
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
              />
              <ErrorDeCampo errores={field.state.meta.errors} />
            </label>
          )}
        </form.Field>

        <form.Field name="rol">
          {(field) => (
            <label>
              Rol
              <br />
              <select
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value as Rol)}
              >
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {ETIQUETA_ROL[r]}
                  </option>
                ))}
              </select>
            </label>
          )}
        </form.Field>

        <div style={{ alignSelf: 'flex-end', display: 'flex', gap: '0.5rem' }}>
          <button type="submit" disabled={actualizar.isPending}>
            {actualizar.isPending ? 'Guardando…' : 'Guardar'}
          </button>
          <button type="button" onClick={onTerminar}>
            Cancelar
          </button>
        </div>
      </div>
      {actualizar.isError && <MensajeError error={actualizar.error} />}
    </form>
  )
}

// --- Tabla (TanStack Table) --------------------------------------------------

const col = createColumnHelper<UsuarioOut>()

interface TablaProps {
  usuarios: UsuarioOut[]
  onEditar: (usuario: UsuarioOut) => void
}

function TablaUsuarios({ usuarios, onEditar }: TablaProps) {
  'use no memo'
  const [sorting, setSorting] = useState<SortingState>([])
  const baja = useDarDeBaja()

  const confirmarBaja = (u: UsuarioOut) => {
    // La baja es lógica (el usuario no se borra), pero deja de poder entrar al sistema.
    if (window.confirm(`¿Dar de baja a ${u.email}? Ya no va a poder ingresar al sistema.`)) {
      baja.mutate(u.id)
    }
  }

  const columnas = useMemo(
    () => [
      col.accessor('nombre', { header: 'Nombre' }),
      col.accessor('email', { header: 'Email' }),
      col.accessor('rol', { header: 'Rol', cell: (i) => ETIQUETA_ROL[i.getValue()] }),
      col.accessor('activo', {
        header: 'Estado',
        cell: (i) => (i.getValue() ? 'Activo' : 'De baja'),
      }),
      col.display({
        id: 'acciones',
        header: 'Acciones',
        cell: (i) => {
          const u = i.row.original
          return (
            <span style={{ display: 'flex', gap: '0.5rem' }}>
              <button type="button" onClick={() => onEditar(u)}>
                Editar
              </button>
              {u.activo && (
                <button type="button" disabled={baja.isPending} onClick={() => confirmarBaja(u)}>
                  Dar de baja
                </button>
              )}
            </span>
          )
        },
      }),
    ],
    // confirmarBaja cambia en cada render; las columnas solo dependen de lo que usan.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [onEditar, baja.isPending],
  )

  // TanStack Table devuelve funciones no memoizables: el compilador de React omite este componente a propósito.
  // eslint-disable-next-line react-hooks/incompatible-library
  const tabla = useReactTable({
    data: usuarios,
    columns: columnas,
    getRowId: (u) => u.id,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  return (
    <>
      <table>
        <thead>
          {tabla.getHeaderGroups().map((grupo) => (
            <tr key={grupo.id}>
              {grupo.headers.map((h) => (
                <th
                  key={h.id}
                  onClick={h.column.getToggleSortingHandler()}
                  style={{ cursor: 'pointer', textAlign: 'left' }}
                >
                  {flexRender(h.column.columnDef.header, h.getContext())}
                  {{ asc: ' ▲', desc: ' ▼' }[h.column.getIsSorted() as string] ?? ''}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {tabla.getRowModel().rows.map((fila) => (
            <tr key={fila.id} style={fila.original.activo ? undefined : { opacity: 0.6 }}>
              {fila.getVisibleCells().map((celda) => (
                <td key={celda.id}>{flexRender(celda.column.columnDef.cell, celda.getContext())}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {baja.isError && <MensajeError error={baja.error} />}
    </>
  )
}
