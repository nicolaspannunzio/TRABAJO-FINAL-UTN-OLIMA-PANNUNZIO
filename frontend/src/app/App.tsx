import { useEffect } from 'react'
import { RouterProvider } from '@tanstack/react-router'
import { useSession } from '../context/session'
import { router } from './router'
import { Cargando } from '../components/Cargando'

export function App() {
  const { session, cargando } = useSession()
  const autenticado = session !== null

  // Cuando se inicia o se cierra sesión, las guardas se reevalúan y redirigen.
  useEffect(() => {
    if (!cargando) void router.invalidate()
  }, [autenticado, cargando])

  if (cargando) return <Cargando />
  return <RouterProvider router={router} context={{ session }} />
}