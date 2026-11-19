import { useState } from 'react'
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from '@tanstack/react-table'
import { RepartoEditor } from './RepartoEditor'
import { Cargando } from '../../components/Cargando'
import { PropiedadForm } from './PropiedadForm'
import { usePropiedades } from './queries'
import type { Propiedad } from './tipos'

const col = createColumnHelper<Propiedad>()

// Referencia estable: un [] nuevo en cada render haría que la tabla se recalcule sin parar.
const SIN_DATOS: Propiedad[] = []

/** HU-03: lista de propiedades con alta y edición. */
export function PropiedadesLista() {
  'use no memo'
  const { data, isPending, isError, error } = usePropiedades()
  const [sorting, setSorting] = useState<SortingState>([])
  // 'nueva' = formulario de alta; un id = edición de esa propiedad; null = ninguno.
  const [formulario, setFormulario] = useState<'nueva' | string | null>(null)
  const [repartoDe, setRepartoDe] = useState<string | null>(null)

  const columnas = [
    col.accessor('direccion', { header: 'Dirección' }),
    col.accessor('localidad', { header: 'Localidad', cell: (i) => i.getValue() ?? '—' }),
    col.accessor('estado', { header: 'Estado' }),
    col.accessor('fecha_alta', {
      header: 'Fecha de alta',
      cell: (i) => new Date(i.getValue()).toLocaleDateString('es-AR'),
    }),
    col.display({
      id: 'acciones',
      header: '',
      cell: (i) => (
        <>
          <button type="button" onClick={() => setFormulario(i.row.original.id)}>Editar</button>{' '}
          <button type="button" onClick={() => setRepartoDe(i.row.original.id)}>Reparto</button>
        </>
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
  if (isError) return <p role="alert">No se pudieron cargar las propiedades: {error.message}</p>

  const enEdicion = data.find((p) => p.id === formulario)

  return (
    <section aria-labelledby="titulo-propiedades">
      <h2 id="titulo-propiedades">Propiedades</h2>
      <button type="button" onClick={() => setFormulario('nueva')} disabled={formulario === 'nueva'}>
        Nueva propiedad
      </button>

      {formulario === 'nueva' && <PropiedadForm onTerminar={() => setFormulario(null)} />}
      {enEdicion && (
        <PropiedadForm key={enEdicion.id} propiedad={enEdicion} onTerminar={() => setFormulario(null)} />
      )}
      {data.some((p) => p.id === repartoDe) && (
        <RepartoEditor key={repartoDe} propiedadId={repartoDe!}
          direccion={data.find((p) => p.id === repartoDe)!.direccion}
          onTerminar={() => setRepartoDe(null)} />
      )}
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
