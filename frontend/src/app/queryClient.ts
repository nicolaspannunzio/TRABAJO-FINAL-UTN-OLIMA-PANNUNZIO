import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query'
import { ApiError } from '../services/api'

// El 401 se resuelve en un solo lugar. Quien arma la app registra qué hacer.
let alExpirarSesion: (() => void) | null = null

export function registrarAlExpirarSesion(fn: () => void) {
  alExpirarSesion = fn
}

function manejarError(error: unknown) {
  if (error instanceof ApiError && error.status === 401) {
    alExpirarSesion?.()
  }
}

export const queryClient = new QueryClient({
  queryCache: new QueryCache({ onError: manejarError }),
  mutationCache: new MutationCache({ onError: manejarError }),
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      // Los errores 4xx son respuestas definitivas: no se reintentan.
      // Sin conexión (status 0) o 5xx sí, por el arranque en frío de Render.
      retry: (intentos, error) => {
        if (error instanceof ApiError && error.status >= 400 && error.status < 500) return false
        return intentos < 2
      },
    },
  },
})