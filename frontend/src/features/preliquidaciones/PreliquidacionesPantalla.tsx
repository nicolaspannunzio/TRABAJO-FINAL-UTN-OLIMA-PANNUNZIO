import { useState } from 'react'
import { useForm } from '@tanstack/react-form'
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table'
import { Cargando } from '../../components/Cargando'
import { ApiError } from '../../services/api'
// checklist y preliquidaciones son los dos de B: se reutiliza la lista de propiedades.
import { usePropiedadesOpciones } from '../checklist/queries'
import { useVersion, useVersiones } from './queries'
import { ResumenPreliquidacion } from './ResumenPreliquidacion'
import type { PreliquidacionResumen } from './tipos'

// El texto se elige según `codigo`, nunca según el mensaje del backend.
function textoError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.codigo) {
      case 'propiedad_no_encontrada':
        return 'La propiedad seleccionada ya no existe.'
      case 'preliquidacion_no_encontrada':
        return 'Esa versión no existe.'
      case 'sin_conexion':
        return 'No se pudo conectar con el servidor. Si recién arranca, probá de nuevo en unos segundos.'
    }
  }
  return 'Ocurrió un error inesperado.'
}

interface Seleccion {
  propiedadId: string
  periodo: string // AAAA-MM-01
}

/** HU-12: historial de versiones de una propiedad y un período, con el detalle de cada una. */
export function PreliquidacionesPantalla() {
  const propiedades = usePropiedadesOpciones()
  const [seleccion, setSeleccion] = useState<Seleccion | null>(null)

  const form = useForm({
    defaultValues: { propiedadId: '', mes: '' },
    onSubmit: ({ value }) => setSeleccion({ propiedadId: value.propiedadId, periodo: `${value.mes}-01` }),
  })

  if (propiedades.isPending) return <Cargando />
  if (propiedades.isError) return <p role="alert">{textoError(propiedades.error)}</p>

  return (
    <section>
      <h1>Preliquidaciones</h1>
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
              <select value={field.state.value} onChange={(e) => field.handleChange(e.target.value)}>
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
          validators={{ onSubmit: ({ value }) => (/^\d{4}-\d{2}$/.test(value) ? undefined : 'Elegí un mes') }}
        >
          {(field) => (
            <label>
              Mes
              <br />
              <input type="month" value={field.state.value} onChange={(e) => field.handleChange(e.target.value)} />
              {field.state.meta.errors.length > 0 && (
                <span role="alert" style={{ display: 'block', color: 'crimson' }}>
                  {field.state.meta.errors.join(', ')}
                </span>
              )}
            </label>
          )}
        </form.Field>
        <button type="submit">Ver versiones</button>
      </form>

      {seleccion && (
        <Historial
          key={`${seleccion.propiedadId}-${seleccion.periodo}`}
          propiedadId={seleccion.propiedadId}
          periodo={seleccion.periodo}
        />
      )}
    </section>
  )
}

// --- Historial de versiones del período --------------------------------------

function Historial({ propiedadId, periodo }: Seleccion) {
  const versiones = useVersiones(propiedadId, periodo)
  // null = mostrar la vigente (la última de la lista).
  const [elegida, setElegida] = useState<string | null>(null)

  if (versiones.isPending) return <Cargando />
  if (versiones.isError) return <p role="alert">{textoError(versiones.error)}</p>
  if (versiones.data.length === 0) {
    return <p style={{ marginTop: '1.5rem' }}>Todavía no se generó ninguna preliquidación para este período.</p>
  }

  const vigenteId = versiones.data[versiones.data.length - 1].id
  const mostrada = elegida ?? vigenteId

  return (
    <div style={{ marginTop: '1.5rem' }}>
      <h2>Versiones</h2>
      <TablaVersiones versiones={versiones.data} vigenteId={vigenteId} mostrada={mostrada} onVer={setElegida} />
      <DetalleVersion key={mostrada} id={mostrada} vigente={mostrada === vigenteId} />
    </div>
  )
}

function DetalleVersion({ id, vigente }: { id: string; vigente: boolean }) {
  const version = useVersion(id)
  if (version.isPending) return <Cargando />
  if (version.isError) return <p role="alert">{textoError(version.error)}</p>
  return <ResumenPreliquidacion preliquidacion={version.data} vigente={vigente} />
}

// --- Tabla de versiones (TanStack Table) -------------------------------------

const col = createColumnHelper<PreliquidacionResumen>()

interface TablaProps {
  versiones: PreliquidacionResumen[]
  vigenteId: string
  mostrada: string
  onVer: (id: string) => void
}

function TablaVersiones({ versiones, vigenteId, mostrada, onVer }: TablaProps) {
  'use no memo'
  const columnas = [
    col.accessor('version', {
      header: 'Versión',
      cell: (i) => (
        <span>
          {i.getValue()}
          {i.row.original.id === vigenteId && <strong style={{ color: '#15803d' }}> (vigente)</strong>}
        </span>
      ),
    }),
    // El importe viaja como cadena decimal: se muestra tal cual, sin convertir a float.
    col.accessor('importe_total', { header: 'Total', cell: (i) => `$ ${i.getValue()}` }),
    col.accessor('generado_en', {
      header: 'Generada',
      cell: (i) => new Date(i.getValue()).toLocaleString('es-AR'),
    }),
    col.display({
      id: 'ver',
      header: '',
      cell: (i) =>
        i.row.original.id === mostrada ? (
          <em>mostrando</em>
        ) : (
          <button type="button" onClick={() => onVer(i.row.original.id)}>
            Ver
          </button>
        ),
    }),
  ]

  // TanStack Table devuelve funciones no memoizables: el compilador de React omite este componente a propósito.
  // eslint-disable-next-line react-hooks/incompatible-library
  const tabla = useReactTable({
    data: versiones,
    columns: columnas,
    getRowId: (v) => v.id,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <table>
      <thead>
        {tabla.getHeaderGroups().map((grupo) => (
          <tr key={grupo.id}>
            {grupo.headers.map((h) => (
              <th key={h.id} style={{ textAlign: 'left' }}>
                {flexRender(h.column.columnDef.header, h.getContext())}
              </th>
            ))}
          </tr>
        ))}
      </thead>
      <tbody>
        {tabla.getRowModel().rows.map((fila) => (
          <tr key={fila.id}>
            {fila.getVisibleCells().map((celda) => (
              <td key={celda.id} style={{ paddingRight: '1rem' }}>
                {flexRender(celda.column.columnDef.cell, celda.getContext())}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
