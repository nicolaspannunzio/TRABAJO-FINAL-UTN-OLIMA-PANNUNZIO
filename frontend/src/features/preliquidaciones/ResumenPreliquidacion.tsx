import type { PreliquidacionOut, TipoAdvertencia } from './tipos'

const ETIQUETA_ADVERTENCIA: Record<TipoAdvertencia, string> = {
  variacion_inusual: '⚠ Variación inusual',
  sin_referencia: 'ℹ Sin referencia',
  total_negativo: '⚠ Total negativo',
  pendiente_confirmado: '⚠ Pendiente confirmado',
}

// Los importes viajan como cadenas decimales: se muestran tal cual, nunca como float.
const pesos = (v: string) => `$ ${v}`

/** Una versión de la preliquidación: cabecera, detalle, advertencias y reparto. */
export function ResumenPreliquidacion({ preliquidacion: p }: { preliquidacion: PreliquidacionOut }) {
  return (
    <article style={{ border: '1px solid #d1d5db', padding: '1rem', marginTop: '1rem' }}>
      <h3 style={{ marginTop: 0 }}>
        Versión {p.version} · total {pesos(p.importe_total)}
      </h3>
      <p style={{ fontSize: '0.9em', color: '#6b7280' }}>
        Generada el {new Date(p.generado_en).toLocaleString('es-AR')}. Es un resumen para revisar,
        no la liquidación oficial.
      </p>

      <h4>Detalle</h4>
      {p.detalle.length === 0 ? (
        <p>Sin conceptos cargados.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>Concepto</th>
              <th style={{ textAlign: 'right' }}>Importe</th>
            </tr>
          </thead>
          <tbody>
            {p.detalle.map((d) => (
              <tr key={d.concepto_id}>
                <td>{d.concepto}</td>
                <td style={{ textAlign: 'right' }}>{pesos(d.importe)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h4>Advertencias</h4>
      {p.advertencias.length === 0 ? (
        <p>Sin advertencias.</p>
      ) : (
        <ul>
          {p.advertencias.map((a, i) => (
            <li key={i}>
              <strong>{ETIQUETA_ADVERTENCIA[a.tipo]}</strong> {a.detalle}
            </li>
          ))}
        </ul>
      )}

      <h4>Reparto</h4>
      <table>
        <thead>
          <tr>
            <th style={{ textAlign: 'left' }}>Propietario</th>
            <th style={{ textAlign: 'right' }}>Porcentaje</th>
            <th style={{ textAlign: 'right' }}>Importe</th>
          </tr>
        </thead>
        <tbody>
          {p.reparto.map((r) => (
            <tr key={r.propietario_id}>
              <td>{r.nombre}</td>
              <td style={{ textAlign: 'right' }}>{r.porcentaje_aplicado} %</td>
              <td style={{ textAlign: 'right' }}>{pesos(r.importe_correspondiente)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </article>
  )
}
