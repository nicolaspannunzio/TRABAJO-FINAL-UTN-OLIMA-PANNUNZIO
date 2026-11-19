import { useState } from 'react'
import { ApiError } from '../../services/api'
import { useGenerarPreliquidacion, useVersiones } from './queries'
import { ResumenPreliquidacion } from './ResumenPreliquidacion'
import type { ConceptoPendiente, PreliquidacionOut } from './tipos'

// El texto se elige según `codigo`, nunca según el mensaje del backend.
function textoError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.codigo) {
      case 'periodo_sin_checklist':
        return 'El período no está abierto.'
      case 'propiedad_sin_reparto':
        return 'La propiedad no tiene propietarios con porcentaje de reparto. Cargalos en "Reparto".'
      case 'reparto_invalido':
        return 'Los porcentajes de reparto de la propiedad no suman 100. Corregilos en "Reparto".'
      case 'version_en_conflicto':
        return 'Otra persona generó este período al mismo tiempo. Volvé a intentar.'
      case 'propiedad_no_encontrada':
        return 'La propiedad ya no existe.'
      case 'sin_conexion':
        return 'No se pudo conectar con el servidor.'
    }
  }
  return 'No se pudo generar la preliquidación.'
}

/** Lee la lista de pendientes del detalle del 409 `pendientes_sin_confirmar`. */
function pendientesDe(error: unknown): ConceptoPendiente[] | null {
  if (!(error instanceof ApiError) || error.codigo !== 'pendientes_sin_confirmar') return null
  const detalle = error.detalle as { pendientes?: ConceptoPendiente[] } | null
  return detalle?.pendientes ?? []
}

interface Props {
  propiedadId: string
  periodo: string
}

/**
 * HU-11: botón para generar la preliquidación del período.
 * Si quedan conceptos pendientes, el backend no genera nada (RN-18) y la pantalla muestra
 * cuáles son; el usuario puede cancelar o confirmar y generar igual.
 *
 * HU-14: si el período ya tiene versiones, el botón genera la siguiente. La nueva pasa a
 * ser la vigente y las anteriores se conservan sin cambios (RN-22, RN-23).
 */
export function GenerarPreliquidacion({ propiedadId, periodo }: Props) {
  const generar = useGenerarPreliquidacion()
  const versiones = useVersiones(propiedadId, periodo)
  const [generada, setGenerada] = useState<PreliquidacionOut | null>(null)

  // Última versión ya generada (la vigente), si hay alguna.
  const vigente = versiones.data?.[versiones.data.length - 1]

  const pendientes = pendientesDe(generar.error)

  const enviar = (confirmar: boolean) => {
    setGenerada(null)
    generar.mutate(
      { propiedad_id: propiedadId, periodo, confirmar_pendientes: confirmar },
      { onSuccess: (p) => setGenerada(p) },
    )
  }

  return (
    <section style={{ marginTop: '1.5rem' }}>
      <h3>Preliquidación</h3>
      {vigente && !generada && (
        <p style={{ fontSize: '0.9em' }}>
          Vigente: <strong>versión {vigente.version}</strong> (total $ {vigente.importe_total}). Si corregiste
          algún importe, generá una nueva versión: será la {vigente.version + 1} y pasará a ser la vigente.
          Las versiones anteriores se conservan sin cambios y se consultan en "Preliquidaciones".
        </p>
      )}
      <button type="button" disabled={generar.isPending} onClick={() => enviar(false)}>
        {generar.isPending ? 'Generando…' : vigente ? 'Generar nueva versión' : 'Generar preliquidación'}
      </button>

      {pendientes && (
        <div role="alertdialog" aria-label="Conceptos pendientes"
             style={{ border: '1px solid #b45309', padding: '0.75rem', marginTop: '0.75rem' }}>
          <p style={{ marginTop: 0 }}>
            <strong>Hay {pendientes.length} concepto{pendientes.length === 1 ? '' : 's'} sin cargar:</strong>
          </p>
          <ul>
            {pendientes.map((p) => (
              <li key={p.concepto_propiedad_id}>{p.concepto}</li>
            ))}
          </ul>
          <p>
            Podés cargarlos antes de generar, o generar igual: cada uno queda registrado como
            "pendiente confirmado" en la preliquidación.
          </p>
          <button type="button" disabled={generar.isPending} onClick={() => enviar(true)}>
            Generar igual
          </button>{' '}
          <button type="button" disabled={generar.isPending} onClick={() => generar.reset()}>
            Cancelar
          </button>
        </div>
      )}

      {generar.isError && !pendientes && (
        <p role="alert" style={{ color: 'crimson' }}>
          {textoError(generar.error)}
        </p>
      )}

      {generada && <ResumenPreliquidacion preliquidacion={generada} vigente />}
    </section>
  )
}
