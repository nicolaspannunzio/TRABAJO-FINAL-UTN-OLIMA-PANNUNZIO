import { useForm } from '@tanstack/react-form'
import { textoError } from './textoError'
import { useActualizarPropietario, useCrearPropietario } from './queries'
import type { Propietario } from './tipos'

interface Props {
  /** Si viene, el formulario edita ese propietario; si no, crea uno nuevo. */
  propietario?: Propietario
  onTerminar: () => void
}

const vacioANull = (v: string) => v.trim() || null

/** HU-03: alta y edición de un propietario. */
export function PropietarioForm({ propietario, onTerminar }: Props) {
  const crear = useCrearPropietario()
  const actualizar = useActualizarPropietario()
  const mutacion = propietario ? actualizar : crear

  const form = useForm({
    defaultValues: {
      nombre: propietario?.nombre ?? '',
      cuit_dni: propietario?.cuit_dni ?? '',
      email: propietario?.email ?? '',
      telefono: propietario?.telefono ?? '',
    },
    onSubmit: ({ value }) => {
      const datos = {
        nombre: value.nombre.trim(),
        cuit_dni: vacioANull(value.cuit_dni),
        email: vacioANull(value.email),
        telefono: vacioANull(value.telefono),
      }
      if (propietario) {
        actualizar.mutate({ id: propietario.id, datos }, { onSuccess: onTerminar })
      } else {
        crear.mutate(datos, { onSuccess: onTerminar })
      }
    },
  })

  const campoOpcional = (name: 'cuit_dni' | 'email' | 'telefono', etiqueta: string) => (
    <form.Field name={name}>
      {(field) => (
        <label>
          {etiqueta} (opcional)
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
  )

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
      {campoOpcional('cuit_dni', 'CUIT / DNI')}
      {campoOpcional('email', 'Email')}
      {campoOpcional('telefono', 'Teléfono')}

      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <button type="submit" disabled={mutacion.isPending}>
          {mutacion.isPending ? 'Guardando…' : propietario ? 'Guardar cambios' : 'Crear propietario'}
        </button>
        <button type="button" onClick={onTerminar} disabled={mutacion.isPending}>
          Cancelar
        </button>
      </div>
      {mutacion.isError && (
        <p role="alert" style={{ color: 'crimson', margin: 0 }}>
          {textoError(mutacion.error, 'guardar el propietario')}
        </p>
      )}
    </form>
  )
}
