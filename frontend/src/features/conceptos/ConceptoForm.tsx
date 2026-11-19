import { useForm } from '@tanstack/react-form'
import { useActualizarConcepto, useCrearConcepto } from './queries'
import { textoError } from './textoError'
import type { Concepto } from './tipos'

interface Props {
  /** Si viene, el formulario edita ese concepto; si no, crea uno nuevo. */
  concepto?: Concepto
  onTerminar: () => void
}

// El umbral viaja como cadena decimal ("30" o "12.5"), nunca como número.
// Number() se usa solo para comprobar que sea mayor que 0.
const normalizar = (v: string) => v.trim().replace(',', '.')

function validarUmbral(valor: string): string | undefined {
  const v = normalizar(valor)
  if (!v) return undefined // vacío = usa el umbral global
  if (!/^\d{1,3}(\.\d{1,2})?$/.test(v)) return 'Ingresá un número con hasta 2 decimales (ej. 30 o 12,5)'
  if (Number(v) <= 0) return 'El umbral tiene que ser mayor que 0'
  return undefined
}

/** HU-05: alta y edición de un concepto, con umbral de variación opcional. */
export function ConceptoForm({ concepto, onTerminar }: Props) {
  const crear = useCrearConcepto()
  const actualizar = useActualizarConcepto()
  const mutacion = concepto ? actualizar : crear

  const form = useForm({
    defaultValues: {
      nombre: concepto?.nombre ?? '',
      tipo: concepto?.tipo ?? '',
      umbral: concepto?.umbral_variacion_pct ?? '',
    },
    onSubmit: ({ value }) => {
      const datos = {
        nombre: value.nombre.trim(),
        tipo: value.tipo.trim() || null,
        // Vacío = null = usa el umbral global (también al editar).
        umbral_variacion_pct: normalizar(value.umbral) || null,
      }
      if (concepto) {
        actualizar.mutate({ id: concepto.id, datos }, { onSuccess: onTerminar })
      } else {
        crear.mutate(datos, { onSuccess: onTerminar })
      }
    },
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        e.stopPropagation()
        void form.handleSubmit()
      }}
      style={{ display: 'grid', gap: '0.5rem', maxWidth: '28rem', margin: '0.75rem 0' }}
    >
      <form.Field
        name="nombre"
        validators={{
          onSubmit: ({ value }) => (value.trim() ? undefined : 'El nombre es obligatorio'),
        }}
      >
        {(field) => (
          <label>
            Nombre
            <input
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              onBlur={field.handleBlur}
              disabled={mutacion.isPending}
              style={{ display: 'block', width: '100%' }}
            />
            {field.state.meta.errors.length > 0 && (
              <span role="alert" style={{ color: 'crimson' }}>
                {field.state.meta.errors.join(', ')}
              </span>
            )}
          </label>
        )}
      </form.Field>

      <form.Field name="tipo">
        {(field) => (
          <label>
            Tipo (opcional)
            <input
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              onBlur={field.handleBlur}
              disabled={mutacion.isPending}
              style={{ display: 'block', width: '100%' }}
            />
          </label>
        )}
      </form.Field>

      <form.Field name="umbral" validators={{ onSubmit: ({ value }) => validarUmbral(value) }}>
        {(field) => (
          <label>
            Umbral de variación en % (opcional)
            <input
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              onBlur={field.handleBlur}
              disabled={mutacion.isPending}
              placeholder="Vacío = usa el umbral global"
              inputMode="decimal"
              style={{ display: 'block', width: '100%' }}
            />
            {field.state.meta.errors.length > 0 && (
              <span role="alert" style={{ color: 'crimson' }}>
                {field.state.meta.errors.join(', ')}
              </span>
            )}
          </label>
        )}
      </form.Field>

      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <button type="submit" disabled={mutacion.isPending}>
          {mutacion.isPending ? 'Guardando…' : concepto ? 'Guardar cambios' : 'Crear concepto'}
        </button>
        <button type="button" onClick={onTerminar} disabled={mutacion.isPending}>
          Cancelar
        </button>
      </div>
      {mutacion.isError && (
        <p role="alert" style={{ color: 'crimson', margin: 0 }}>
          {textoError(mutacion.error, 'guardar el concepto')}
        </p>
      )}
    </form>
  )
}