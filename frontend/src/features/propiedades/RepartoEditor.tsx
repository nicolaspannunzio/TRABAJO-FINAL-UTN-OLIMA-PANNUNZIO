import { useState } from 'react'
import { Cargando } from '../../components/Cargando'
import { useGuardarReparto, usePropietarios, useReparto } from './queries'
import { textoError } from './textoError'
import type { RepartoVigente } from './tipos'

const FORMATO = /^\d{1,3}(\.\d{1,2})?$/
const aCentesimas = (texto: string) =>
  FORMATO.test(texto.trim()) ? Math.round(Number(texto.trim()) * 100) : null
const aTexto = (centesimas: number) => (centesimas / 100).toFixed(2)

interface Props {
  propiedadId: string
  direccion: string
  onTerminar: () => void
}

/** HU-04: editor de porcentajes con la suma visible. */
export function RepartoEditor({ propiedadId, direccion, onTerminar }: Props) {
  const reparto = useReparto(propiedadId)
  if (reparto.isPending) return <Cargando />
  if (reparto.isError) return <p role="alert">{textoError(reparto.error, 'cargar el reparto')}</p>
  // key: si el reparto cambia en el servidor, las filas se vuelven a armar desde cero.
  return (
    <FilasReparto key={JSON.stringify(reparto.data)} propiedadId={propiedadId}
      direccion={direccion} inicial={reparto.data} onTerminar={onTerminar} />
  )
}

interface FilasProps extends Props {
  inicial: RepartoVigente[]
}

function FilasReparto({ propiedadId, direccion, inicial, onTerminar }: FilasProps) {
  const propietarios = usePropietarios()
  const guardar = useGuardarReparto(propiedadId)
  const [filas, setFilas] = useState(() =>
    inicial.map((r) => ({ propietario_id: r.propietario_id, porcentaje: r.porcentaje })),
  )

  const centesimas = filas.map((f) => aCentesimas(f.porcentaje))
  const hayInvalidas = centesimas.some((c) => c === null || c <= 0 || c > 10000)
  const suma = centesimas.reduce<number>((total, c) => total + (c ?? 0), 0)
  const sumaOk = suma === 10000
  const puedeGuardar = filas.length > 0 && !hayInvalidas && sumaOk && !guardar.isPending

  const nombre = (id: string) =>
    propietarios.data?.find((p) => p.id === id)?.nombre ??
    inicial.find((r) => r.propietario_id === id)?.nombre ??
    id
  const libres = (propietarios.data ?? []).filter(
    (p) => p.estado === 'activa' && !filas.some((f) => f.propietario_id === p.id),
  )

  const cambiar = (indice: number, porcentaje: string) =>
    setFilas((actual) => actual.map((f, i) => (i === indice ? { ...f, porcentaje } : f)))

  const guardarReparto = () =>
    guardar.mutate(
      filas.map((f, i) => ({ propietario_id: f.propietario_id, porcentaje: aTexto(centesimas[i]!) })),
      { onSuccess: onTerminar },
    )

  return (
    <section aria-label={`Reparto de ${direccion}`}>
      <h3>Reparto de {direccion}</h3>
      {filas.length === 0 && <p>Esta propiedad todavía no tiene propietarios.</p>}
      <table>
        <tbody>
          {filas.map((fila, i) => (
            <tr key={fila.propietario_id}>
              <td>{nombre(fila.propietario_id)}</td>
              <td>
                <input aria-label={`Porcentaje de ${nombre(fila.propietario_id)}`}
                  inputMode="decimal" value={fila.porcentaje}
                  aria-invalid={centesimas[i] === null || centesimas[i]! <= 0 || centesimas[i]! > 10000}
                  onChange={(e) => cambiar(i, e.target.value)} disabled={guardar.isPending} /> %
              </td>
              <td>
                <button type="button" disabled={guardar.isPending}
                  onClick={() => setFilas((actual) => actual.filter((_, j) => j !== i))}>
                  Quitar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <select value="" disabled={guardar.isPending || libres.length === 0}
        onChange={(e) => e.target.value &&
          setFilas((actual) => [...actual, { propietario_id: e.target.value, porcentaje: '' }])}>
        <option value="">Agregar propietario…</option>
        {libres.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
      </select>

      <p role="status">
        Suma: <strong>{aTexto(suma)} %</strong>{' '}
        {sumaOk ? '✓' : suma < 10000 ? `(faltan ${aTexto(10000 - suma)})` : `(sobran ${aTexto(suma - 10000)})`}
      </p>
      {hayInvalidas && <p role="alert">Cada porcentaje debe ser mayor que 0 y hasta 100, con hasta 2 decimales.</p>}
      {guardar.isError && <p role="alert">{textoError(guardar.error, 'guardar el reparto')}</p>}

      <button type="button" onClick={guardarReparto} disabled={!puedeGuardar}>Guardar reparto</button>{' '}
      <button type="button" onClick={onTerminar} disabled={guardar.isPending}>Cancelar</button>
    </section>
  )
}