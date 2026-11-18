import { useForm } from '@tanstack/react-form'
import { textoError } from './textoError'
import { useActualizarPropiedad, useCrearPropiedad } from './queries'
import type { Propiedad } from './tipos'

interface Props {
  /** Si viene, el formulario edita esa propiedad; si no, crea una nueva. */
  propiedad?: Propiedad
  onTerminar: () => void
}

/** HU-03: alta y edición de una propiedad. La propiedad nueva queda `activa`. */
export function PropiedadForm({ propiedad, onTerminar }: Props) {
  const crear = useCrearPropiedad()
  const actualizar = useActualizarPropiedad()
  const mutacion = propiedad ? actualizar : crear

  const form = useForm({
    defaultValues: {
      direccion: propiedad?.direccion ?? '',
      localidad: propiedad?.localidad ?? '',
      estado: propiedad?.estado ?? 'activa',
    },
    onSubmit: ({ value }) => {
      const datos = {
        direccion: value.direccion.trim(),
        localidad: value.localidad.trim() || null,
      }
      if (propiedad) {
        actualizar.mutate(
          { id: propiedad.id, datos: { ...datos, estado: value.estado } },
          { onSuccess: onTerminar },
        )
      } else {
        crear.mutate({ ...datos, estado: 'activa' }, { onSuccess: onTerminar })
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
        name="direccion"
        validators={{
          onSubmit: ({ value }) => (value.trim() ? undefined : 'La dirección es obligatoria'),
        }}
      >
        {(field) => (
          <label>
            Dirección
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

      <form.Field name="localidad">
        {(field) => (
          <label>
            Localidad (opcional)
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

      {propiedad && (
        <form.Field name="estado">
          {(field) => (
            <label>
              Estado
              <select
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value as Propiedad['estado'])}
                disabled={mutacion.isPending}
                style={{ display: 'block' }}
              >
                <option value="activa">Activa</option>
                <option value="inactiva">Inactiva</option>
              </select>
            </label>
          )}
        </form.Field>
      )}

      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <button type="submit" disabled={mutacion.isPending}>
          {mutacion.isPending ? 'Guardando…' : propiedad ? 'Guardar cambios' : 'Crear propiedad'}
        </button>
        <button type="button" onClick={onTerminar} disabled={mutacion.isPending}>
          Cancelar
        </button>
      </div>
      {mutacion.isError && (
        <p role="alert" style={{ color: 'crimson', margin: 0 }}>
          {textoError(mutacion.error, 'guardar la propiedad')}
        </p>
      )}
    </form>
  )
}
