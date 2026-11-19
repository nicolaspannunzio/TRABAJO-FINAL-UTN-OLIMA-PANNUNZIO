import { useState } from 'react'
import { useForm } from '@tanstack/react-form'
import { ApiError } from '../../services/api'
import type { FilaChecklist } from '../checklist/tipos'
import { useCorregirImporte } from './queries'

// Acepta "68200", "68200.50", "68200,50" y negativos ("-2000"). Sin separador de miles.
const FORMATO_IMPORTE = /^-?\d{1,12}([.,]\d{1,2})?$/

// El importe sigue siendo una cadena decimal: solo se cambia la coma por punto, nunca float.
function normalizar(valor: string): string {
  return valor.trim().replace(',', '.')
}

// El texto se elige según `codigo`, nunca según el mensaje del backend.
function textoError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.codigo) {
      case 'importe_no_encontrado':
        return 'El importe ya no existe. Volvé a cargar el período.'
      case 'validacion':
        return 'El importe no es válido.'
      case 'sin_conexion':
        return 'No se pudo conectar con el servidor.'
    }
  }
  return 'No se pudo corregir el importe.'
}

interface Props {
  fila: FilaChecklist
  propiedadId: string
  periodo: string
}

/**
 * HU-13: corrige el importe de una fila `cargado`.
 * Las preliquidaciones ya generadas no cambian: para usar el valor corregido hay que
 * generar una versión nueva.
 */
export function CorregirImporte({ fila, propiedadId, periodo }: Props) {
  const [editando, setEditando] = useState(false)
  const corregir = useCorregirImporte(propiedadId, periodo)

  const form = useForm({
    defaultValues: { importe: fila.importe ?? '' },
    onSubmit: ({ value }) => {
      if (!fila.importe_id) return
      corregir.mutate(
        { importeId: fila.importe_id, datos: { importe: normalizar(value.importe) } },
        { onSuccess: () => setEditando(false) },
      )
    },
  })

  if (fila.estado !== 'cargado' || !fila.importe_id) return null

  if (!editando) {
    return (
      <button
        type="button"
        onClick={() => {
          form.reset()
          corregir.reset()
          setEditando(true)
        }}
      >
        Corregir importe
      </button>
    )
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        e.stopPropagation()
        void form.handleSubmit()
      }}
    >
      <form.Field
        name="importe"
        validators={{
          onSubmit: ({ value }) =>
            FORMATO_IMPORTE.test(value.trim()) ? undefined : 'Ej.: 68200,50 o -2000 (sin puntos de miles)',
        }}
      >
        {(field) => (
          <span>
            <input
              aria-label={`Nuevo importe de ${fila.concepto}`}
              inputMode="decimal"
              size={12}
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              disabled={corregir.isPending}
            />{' '}
            <button type="submit" disabled={corregir.isPending}>
              {corregir.isPending ? 'Guardando…' : 'Guardar'}
            </button>{' '}
            <button type="button" disabled={corregir.isPending} onClick={() => setEditando(false)}>
              Cancelar
            </button>
            {field.state.meta.errors.length > 0 && (
              <span role="alert" style={{ display: 'block', color: 'crimson' }}>
                {field.state.meta.errors.join(', ')}
              </span>
            )}
          </span>
        )}
      </form.Field>
      <span style={{ display: 'block', fontSize: '0.85em', color: '#6b7280' }}>
        Las preliquidaciones ya generadas no cambian: generá una versión nueva para usar este valor.
      </span>
      {corregir.isError && (
        <span role="alert" style={{ display: 'block', color: 'crimson' }}>
          {textoError(corregir.error)}
        </span>
      )}
    </form>
  )
}
