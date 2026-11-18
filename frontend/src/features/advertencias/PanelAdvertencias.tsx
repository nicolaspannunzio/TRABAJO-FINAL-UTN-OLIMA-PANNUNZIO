import type { FilaChecklist } from '../checklist/tipos'
import { useAdvertencias } from './queries'
import type { AdvertenciaPrevia } from './tipos'

const ETIQUETA: Record<AdvertenciaPrevia['tipo'], string> = {
  variacion_inusual: '⚠ Variación inusual',
  sin_referencia: 'ℹ Sin referencia',
  total_negativo: '⚠ Total negativo',
  pendiente_confirmado: '⚠ Pendiente confirmado',
}

const COLOR: Record<AdvertenciaPrevia['tipo'], string> = {
  variacion_inusual: '#b45309',
  sin_referencia: '#2563eb',
  total_negativo: '#b45309',
  pendiente_confirmado: '#b45309',
}

interface Props {
  propiedadId: string
  periodo: string
  filas: FilaChecklist[]
}

/**
 * HU-10: advertencias del período, visibles en el checklist.
 * Son informativas: no bloquean nada (RN-17).
 */
export function PanelAdvertencias({ propiedadId, periodo, filas }: Props) {
  // Cambia cada vez que se carga un importe o se marca un concepto: dispara el recálculo.
  const version = filas.map((f) => `${f.id}:${f.estado}:${f.importe ?? ''}`).join('|')
  const advertencias = useAdvertencias(propiedadId, periodo, version)

  if (advertencias.isPending) return <p>Calculando advertencias…</p>
  if (advertencias.isError) return <p role="alert">No se pudieron calcular las advertencias.</p>

  return (
    <section style={{ marginTop: '1rem' }}>
      <h3>Advertencias</h3>
      <p style={{ fontSize: '0.9em', color: '#6b7280' }}>
        Comparan cada importe cargado con el del mes anterior. Son solo avisos: no impiden generar
        la preliquidación.
      </p>
      {advertencias.data.length === 0 ? (
        <p>Sin advertencias.</p>
      ) : (
        <ul>
          {advertencias.data.map((a) => (
            <li key={`${a.concepto_propiedad_id}-${a.tipo}`}>
              <strong style={{ color: COLOR[a.tipo] }}>{ETIQUETA[a.tipo]}</strong> {a.detalle}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
