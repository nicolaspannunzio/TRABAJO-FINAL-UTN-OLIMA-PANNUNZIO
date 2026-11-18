import { useState } from 'react'
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
import { useAbrirPeriodo, useChecklist, usePropiedadesOpciones } from './queries'
import type { EstadoChecklist, FilaChecklist } from './tipos'

// --- Textos de la interfaz ---------------------------------------------------

const ETIQUETA_ESTADO: Record<EstadoChecklist, string> = {
  pendiente: 'Pendiente',
  cargado: 'Cargado',
  no_corresponde: 'No corresponde',
}

// El texto se elige según `codigo`, nunca según el mensaje del backend.
function textoError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.codigo) {
      case 'propiedad_no_encontrada':
        return 'La propiedad seleccionada ya no existe.'
      case 'validacion':
        return 'El período debe ser un mes válido.'
      case 'sin_conexion':
        return 'No se pudo conectar con el servidor. Si recién arranca, probá de nuevo en unos segundos.'
    }
  }
  return 'Ocurrió un error inesperado.'
}

// "2026-09-01" → "septiembre de 2026", sin pasar por zonas horarias.
function nombreDelMes(periodo: string): string {
  const anio = Number(periodo.slice(0, 4))
  const mes = Number(periodo.slice(5, 7))
  return new Date(anio, mes - 1, 1).toLocaleDateString('es-AR', { month: 'long', year: 'numeric' })
}

// --- Pantalla ----------------------------------------------------------------

interface Seleccion {
  propiedadId: string
  periodo: string // AAAA-MM-01
}

export function ChecklistPantalla() {
  const propiedades = usePropiedadesOpciones()
  const [seleccion, setSeleccion] = useState<Seleccion | null>(null)

  const form = useForm({
    defaultValues: { propiedadId: '', mes: '' }, // mes: "AAAA-MM" del <input type="month">
    onSubmit: ({ value }) => {
      setSeleccion({ propiedadId: value.propiedadId, periodo: `${value.mes}-01` })
    },
  })

  if (propiedades.isPending) return <Cargando />
  if (propiedades.isError) {
    return <p role="alert">No se pudieron cargar las propiedades: {textoError(propiedades.error)}</p>
  }

  return (
    <section>
      <h1>Checklist del período</h1>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          e.stopPropagation()
          void form.handleSubmit()
        }}
        style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}
      >
        <form.Field
          name="propiedadId"
          validators={{ onSubmit: ({ value }) => (value ? undefined : 'Elegí una propiedad') }}
        >
          {(field) => (
            <label>
              Propiedad
              <br />
              <select
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
              >
                <option value="">Seleccioná…</option>
                {propiedades.data.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.direccion}
                    {p.localidad ? ` (${p.localidad})` : ''}
                  </option>
                ))}
              </select>
              {field.state.meta.errors.length > 0 && (
                <span role="alert" style={{ display: 'block', color: 'crimson' }}>
                  {field.state.meta.errors.join(', ')}
                </span>
              )}
            </label>
          )}
        </form.Field>

        <form.Field
          name="mes"
          validators={{
            onSubmit: ({ value }) => (/^\d{4}-\d{2}$/.test(value) ? undefined : 'Elegí un mes'),
          }}
        >
          {(field) => (
            <label>
              Mes
              <br />
              <input
                type="month"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
              />
              {field.state.meta.errors.length > 0 && (
                <span role="alert" style={{ display: 'block', color: 'crimson' }}>
                  {field.state.meta.errors.join(', ')}
                </span>
              )}
            </label>
          )}
        </form.Field>

        <button type="submit">Ver período</button>
      </form>

      {seleccion && (
        <ChecklistDelPeriodo
          key={`${seleccion.propiedadId}-${seleccion.periodo}`}
          propiedadId={seleccion.propiedadId}
          periodo={seleccion.periodo}
        />
      )}
    </section>
  )
}

// --- Checklist de una propiedad y un período ---------------------------------

function ChecklistDelPeriodo({ propiedadId, periodo }: Seleccion) {
  const checklist = useChecklist(propiedadId, periodo)
  const abrir = useAbrirPeriodo()

  if (checklist.isPending) return <Cargando />
  if (checklist.isError) return <p role="alert">{textoError(checklist.error)}</p>

  if (checklist.data === null) {
    return (
      <div style={{ marginTop: '1.5rem' }}>
        <p>El período {nombreDelMes(periodo)} todavía no está abierto para esta propiedad.</p>
        <button
          type="button"
          disabled={abrir.isPending}
          onClick={() => abrir.mutate({ propiedad_id: propiedadId, periodo })}
        >
          {abrir.isPending ? 'Abriendo…' : 'Abrir período'}
        </button>
        {abrir.isError && <p role="alert">{textoError(abrir.error)}</p>}
      </div>
    )
  }

  const filas = checklist.data.filas
  const pendientes = filas.filter((f) => f.estado === 'pendiente').length

  return (
    <div style={{ marginTop: '1.5rem' }}>
      <h2>Período {nombreDelMes(periodo)}</h2>
      {filas.length === 0 ? (
        <p>La plantilla de esta propiedad no tiene conceptos activos.</p>
      ) : (
        <>
          <p>
            {filas.length} conceptos · {pendientes} pendiente{pendientes === 1 ? '' : 's'}
          </p>
          <TablaChecklist filas={filas} />
        </>
      )}
    </div>
  )
}

// --- Tabla (TanStack Table) --------------------------------------------------

const col = createColumnHelper<FilaChecklist>()

const columnas = [
  col.accessor('concepto', { header: 'Concepto' }),
  col.accessor('estado', {
    header: 'Estado',
    cell: (i) => <span data-estado={i.getValue()}>{ETIQUETA_ESTADO[i.getValue()]}</span>,
  }),
  col.accessor('importe', {
    header: 'Importe',
    // El importe viaja como cadena decimal: se muestra tal cual, sin convertir a float.
    cell: (i) => {
      const v = i.getValue()
      return v == null ? '—' : `$ ${v}`
    },
  }),
]

function TablaChecklist({ filas }: { filas: FilaChecklist[] }) {
  'use no memo'
  const [sorting, setSorting] = useState<SortingState>([])

  // TanStack Table devuelve funciones no memoizables: el compilador de React omite este componente a propósito.
  // eslint-disable-next-line react-hooks/incompatible-library
  const tabla = useReactTable({
    data: filas,
    columns: columnas,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  return (
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
          <tr key={fila.id}>
            {fila.getVisibleCells().map((celda) => (
              <td key={celda.id}>{flexRender(celda.column.columnDef.cell, celda.getContext())}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}