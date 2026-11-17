import { createFileRoute } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../../services/api'
import { useSession } from '../../../context/session'

export const Route = createFileRoute('/_autenticado/')({
  component: Inicio,
})

function Inicio() {
  const { cerrarSesion } = useSession()
  const me = useQuery({
    queryKey: ['me'],
    queryFn: () => apiFetch<{ nombre: string; rol: string }>('/me'),
  })

  return (
    <div>
      <p>
        {me.isPending
          ? 'cargando…'
          : me.isError
            ? `error: ${me.error.message}`
            : `${me.data.nombre} (${me.data.rol})`}
      </p>
      <button onClick={() => void cerrarSesion()}>Cerrar sesión</button>
    </div>
  )
}