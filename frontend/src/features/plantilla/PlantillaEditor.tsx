import { useState } from 'react'
import { Cargando } from '../../components/Cargando'
import { useConceptos } from '../conceptos/queries'
import { useAsociarConcepto, useCambiarActivo, usePlantilla } from './queries'
import { textoError } from './textoError'

interface Props {
  propiedadId: string
  direccion: string
  onTerminar: () => void
}

/** HU-06: plantilla de la propiedad. De acá sale el checklist de los períodos que se abran después. */
export function PlantillaEditor({ propiedadId, direccion, onTerminar }: Props) {
  const plantilla = usePlantilla(propiedadId)
  const conceptos = useConceptos()
  const asociar = useAsociarConcepto(propiedadId)
  const cambiar = useCambiarActivo(propiedadId)
  const [elegido, setElegido] = useState('')

  if (plantilla.isPending) return <Cargando />
  if (plantilla.isError) {
    return <p role="alert">{textoError(plantilla.error, 'cargar la plantilla')}</p>
  }

  // Solo se ofrecen los conceptos que todavía no están en la plantilla (activos o no).
  const libres = (conceptos.data ?? []).filter(
    (c) => !plantilla.data.some((f) => f.concepto_id === c.id),
  )
  const ocupado = asociar.isPending || cambiar.isPending

  const agregar = () =>
    asociar.mutate(elegido, { onSuccess: () => setElegido('') })

  return (
    <section aria-label={`Plantilla de ${direccion}`}>
      <h3>Plantilla de {direccion}</h3>
      {plantilla.data.length === 0 ? (
        <p>Esta propiedad todavía no tiene conceptos asociados.</p>
      ) : (
        <table>
          <thead>
            <tr><th style={{ textAlign: 'left' }}>Concepto</th><th>Estado</th><th /></tr>
          </thead>
          <tbody>
            {plantilla.data.map((fila) => (
              <tr key={fila.id}>
                <td>{fila.concepto}</td>
                <td>{fila.activo ? 'Activo' : 'Inactivo'}</td>
                <td>
                  <button type="button" disabled={ocupado}
                    onClick={() => cambiar.mutate({ id: fila.id, activo: !fila.activo })}>
                    {fila.activo ? 'Desactivar' : 'Activar'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <select aria-label="Concepto a asociar" value={elegido} disabled={ocupado || libres.length === 0}
        onChange={(e) => setElegido(e.target.value)}>
        <option value="">Asociar concepto…</option>
        {libres.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
      </select>{' '}
      <button type="button" onClick={agregar} disabled={!elegido || ocupado}>Asociar</button>

      {asociar.isError && <p role="alert">{textoError(asociar.error, 'asociar el concepto')}</p>}
      {cambiar.isError && <p role="alert">{textoError(cambiar.error, 'cambiar el estado del concepto')}</p>}

      <p><button type="button" onClick={onTerminar}>Cerrar</button></p>
    </section>
  )
}