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
import { usePropiedades } from './queries'
import type { Propiedad } from './tipos'

const col = createColumnHelper<Propiedad>()

const columnas = [
  col.accessor('direccion', { header: 'Dirección' }),
  col.accessor('localidad', { header: 'Localidad', cell: (i) => i.getValue() ?? '—' }),
  col.accessor('estado', { header: 'Estado' }),
  col.accessor('fecha_alta', {
    header: 'Fecha de alta',
    cell: (i) => new Date(i.getValue()).toLocaleDateString('es-AR'),
  }),
]

// Referencia estable: un [] nuevo en cada render haría que la tabla se recalcule sin parar.
const SIN_DATOS: Propiedad[] = []

export function PropiedadesPantalla() {
  'use no memo'
  const { data, isPending, isError, error } = usePropiedades()
  const [sorting, setSorting] = useState<SortingState>([])

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
  if (isError) return <p role="alert">No se pudieron cargar las propiedades: {error.message}</p>

  return (
    <section>
      <h1>Propiedades</h1>
      {data.length === 0 ? (
        <p>No hay propiedades cargadas.</p>
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