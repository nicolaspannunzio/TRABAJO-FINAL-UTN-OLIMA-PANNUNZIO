import { useForm } from '@tanstack/react-form'
import { ApiError } from '../../services/api'
import type { FilaChecklist } from '../checklist/tipos'
import { useCargarImporte } from './queries'

// Acepta "15000", "15000.50", "15000,50" y negativos ("-2000"). Sin separador de miles.
const FORMATO_IMPORTE = /^-?\d{1,12}([.,]\d{1,2})?$/

// El importe sigue siendo una cadena decimal: solo se cambia la coma por punto, nunca float.
function normalizar(valor: string): string {
  return valor.trim().replace(',', '.')
}

// El texto se elige según `codigo`, nunca según el mensaje del backend.
function textoError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.codigo) {
      case 'importe_duplicado':
        return 'Este concepto ya tiene un importe cargado en el período. Se conservó el primero.'
      case 'concepto_sin_fila_checklist':
        return 'El concepto no forma parte del checklist de este período.'
      case 'validacion':
        return 'El importe no es válido.'
      case 'sin_conexion':
        return 'No se pudo conectar con el servidor.'
    }
  }
  return 'No se pudo cargar el importe.'
}

interface Props {
  fila: FilaChecklist
  propiedadId: string
  periodo: string
}

/** HU-08: carga del importe de una fila `pendiente` del checklist. */
export function CargaImporte({ fila, propiedadId, periodo }: Props) {
  const cargar = useCargarImporte()

  const form = useForm({
    defaultValues: { importe: '' },
    onSubmit: ({ value }) => {
      cargar.mutate({
        propiedad_id: propiedadId,
        periodo,
        concepto_propiedad_id: fila.concepto_propiedad_id,
        importe: normalizar(value.importe),
      })
    },
  })

  if (fila.estado !== 'pendiente') return null

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        e.stopPropagation()
        void form.handleSubmit()
      }}
      style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}
    >
      <form.Field
        name="importe"
        validators={{
          onSubmit: ({ value }) =>
            FORMATO_IMPORTE.test(value.trim()) ? undefined : 'Ej.: 15000,50 o -2000 (sin puntos de miles)',
        }}
      >
        {(field) => (
          <span>
            <input
              aria-label={`Importe de ${fila.concepto}`}
              inputMode="decimal"
              placeholder="0,00"
              size={12}
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              onBlur={field.handleBlur}
              disabled={cargar.isPending}
            />
            {field.state.meta.errors.length > 0 && (
              <span role="alert" style={{ display: 'block', color: 'crimson' }}>
                {field.state.meta.errors.join(', ')}
              </span>
            )}
          </span>
        )}
      </form.Field>
      <button type="submit" disabled={cargar.isPending}>
        {cargar.isPending ? 'Cargando…' : 'Cargar'}
      </button>
      {cargar.isError && (
        <span role="alert" style={{ color: 'crimson' }}>
          {textoError(cargar.error)}
        </span>
      )}
    </form>
  )
}
