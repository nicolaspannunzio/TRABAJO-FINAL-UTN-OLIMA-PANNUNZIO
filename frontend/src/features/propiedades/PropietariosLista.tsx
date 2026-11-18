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
import { PropietarioForm } from './PropietarioForm'
import { usePropietarios } from './queries'
import type { Propietario } from './tipos'

const col = createColumnHelper<Propietario>()

const SIN_DATOS: Propietario[] = []

/** HU-03: lista de propietarios con alta y edición. */
export function PropietariosLista() {
  'use no memo'
  const { data, isPending, isError, error } = usePropietarios()
  const [sorting, setSorting] = useState<SortingState>([])
  const [formulario, setFormulario] = useState<'nuevo' | string | null>(null)

  const columnas = [
    col.accessor('nombre', { header: 'Nombre' }),
    col.accessor('cuit_dni', { header: 'CUIT / DNI', cell: (i) => i.getValue() ?? '—' }),
    col.accessor('email', { header: 'Email', cell: (i) => i.getValue() ?? '—' }),
    col.accessor('telefono', { header: 'Teléfono', cell: (i) => i.getValue() ?? '—' }),
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
  if (isError) return <p role="alert">No se pudieron cargar los propietarios: {error.message}</p>

  const enEdicion = data.find((p) => p.id === formulario)

  return (
    <section aria-labelledby="titulo-propietarios">
      <h2 id="titulo-propietarios">Propietarios</h2>
      <button type="button" onClick={() => setFormulario('nuevo')} disabled={formulario === 'nuevo'}>
        Nuevo propietario
      </button>

      {formulario === 'nuevo' && <PropietarioForm onTerminar={() => setFormulario(null)} />}
      {enEdicion && (
        <PropietarioForm key={enEdicion.id} propietario={enEdicion} onTerminar={() => setFormulario(null)} />
      )}

      {data.length === 0 ? (
        <p>No hay propietarios cargados.</p>
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
