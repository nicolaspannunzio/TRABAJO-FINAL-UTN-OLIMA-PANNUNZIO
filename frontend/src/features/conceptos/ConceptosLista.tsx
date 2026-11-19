import { useState } from 'react'
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from '@tanstack/react-table'
import { Cargando } from '../../components/Cargando'
import { ConceptoForm } from './ConceptoForm'
import { useConceptos } from './queries'
import type { Concepto } from './tipos'

const col = createColumnHelper<Concepto>()

// Referencia estable: un [] nuevo en cada render haría que la tabla se recalcule sin parar.
const SIN_DATOS: Concepto[] = []

/** HU-05: catálogo de conceptos con alta y edición. */
export function ConceptosLista() {
  'use no memo'
  const { data, isPending, isError, error } = useConceptos()
  const [sorting, setSorting] = useState<SortingState>([])
  // 'nuevo' = formulario de alta; un id = edición de ese concepto; null = ninguno.
  const [formulario, setFormulario] = useState<'nuevo' | string | null>(null)

  const columnas = [
    col.accessor('nombre', { header: 'Nombre' }),
    col.accessor('tipo', { header: 'Tipo', cell: (i) => i.getValue() ?? '—' }),
    col.accessor('umbral_variacion_pct', {
      header: 'Umbral de variación',
      cell: (i) => (i.getValue() ? `${i.getValue()} %` : 'Global'),
    }),
    col.display({
      id: 'acciones',
      header: '',
      cell: (i) => (
        <button type="button" onClick={() => setFormulario(i.row.original.id)}>
          Editar
        </button>
      ),
    }),
  ]

  // TanStack Table devuelve funciones no memoizables: el compilador de React omite este componente a propósito.
  // eslint-disable-next-line react-hooks/incompatible-library
  const tabla = useReactTable({
    data: data ?? SIN_DATOS,
    columns: columnas,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  if (isPending) return <Cargando />
  if (isError) return <p role="alert">No se pudieron cargar los conceptos: {error.message}</p>

  const enEdicion = data.find((c) => c.id === formulario)

  return (
    <section aria-labelledby="titulo-conceptos">
      <h2 id="titulo-conceptos">Catálogo de conceptos</h2>
      <button type="button" onClick={() => setFormulario('nuevo')} disabled={formulario === 'nuevo'}>
        Nuevo concepto
      </button>

      {formulario === 'nuevo' && <ConceptoForm onTerminar={() => setFormulario(null)} />}
      {enEdicion && (
        <ConceptoForm key={enEdicion.id} concepto={enEdicion} onTerminar={() => setFormulario(null)} />
      )}

      {data.length === 0 ? (
        <p>No hay conceptos cargados.</p>
      ) : (
        <table>
          <thead>
            {tabla.getHeaderGroups().map((grupo) => (
              <tr key={grupo.id}>
                {grupo.headers.map((h) => (
                  <th key={h.id} onClick={h.column.getToggleSortingHandler()} style={{ cursor: 'pointer', textAlign: 'left' }}>
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
      )}
    </section>
  )
}