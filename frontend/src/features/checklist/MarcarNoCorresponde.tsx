import { useState } from 'react'
import { ApiError } from '../../services/api'
import { useMarcarNoCorresponde } from './queries'
import type { FilaChecklist } from './tipos'

function textoError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.codigo) {
      case 'fila_no_encontrada':
        return 'La fila ya no existe. Volvé a cargar el período.'
      case 'sin_conexion':
        return 'No se pudo conectar con el servidor.'
    }
  }
  return 'No se pudo marcar el concepto.'
}

interface Props {
  fila: FilaChecklist
  propiedadId: string
  periodo: string
}

/**
 * HU-09: marcar una fila `pendiente` o `cargado` como no corresponde.
 * Pide confirmación antes de llamar al backend; si la fila está cargada, avisa que se
 * elimina el importe. Si se cancela, no cambia nada.
 */
export function MarcarNoCorresponde({ fila, propiedadId, periodo }: Props) {
  const [confirmando, setConfirmando] = useState(false)
  const marcar = useMarcarNoCorresponde(propiedadId, periodo)

  if (fila.estado === 'no_corresponde') return null

  if (!confirmando) {
    return (
      <button type="button" onClick={() => setConfirmando(true)}>
        No corresponde
      </button>
    )
  }

  return (
    <span role="group" aria-label={`Confirmar no corresponde para ${fila.concepto}`}>
      <span style={{ display: 'block' }}>
        {fila.estado === 'cargado'
          ? `Se eliminará el importe de $ ${fila.importe}. ¿Marcar "${fila.concepto}" como no corresponde?`
          : `¿Marcar "${fila.concepto}" como no corresponde?`}
      </span>
      <button
        type="button"
        disabled={marcar.isPending}
        onClick={() => marcar.mutate(fila.id, { onSuccess: () => setConfirmando(false) })}
      >
        {marcar.isPending ? 'Marcando…' : 'Confirmar'}
      </button>{' '}
      <button
        type="button"
        disabled={marcar.isPending}
        onClick={() => {
          marcar.reset()
          setConfirmando(false)
        }}
      >
        Cancelar
      </button>
      {marcar.isError && (
        <span role="alert" style={{ display: 'block', color: 'crimson' }}>
          {textoError(marcar.error)}
        </span>
      )}
    </span>
  )
}
