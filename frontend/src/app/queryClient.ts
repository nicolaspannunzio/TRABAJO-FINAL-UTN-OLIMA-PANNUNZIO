import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query'
import { ApiError } from '../services/api'

export type MotivoCierre = 'sesion_expirada' | 'usuario_inactivo'

// El cierre forzado de sesión se resuelve en un solo lugar. Quien arma la app registra qué hacer.
let alExpirarSesion: ((motivo: MotivoCierre) => void) | null = null
let motivoPendiente: MotivoCierre | null = null

export function registrarAlExpirarSesion(fn: (motivo: MotivoCierre) => void) {
  alExpirarSesion = fn
}

// El motivo viaja hasta el login para explicarle al usuario por qué lo sacaron.
export function fijarMotivoCierre(motivo: MotivoCierre) {
  motivoPendiente = motivo
}
export function leerMotivoCierre(): MotivoCierre | null {
  return motivoPendiente
}
export function limpiarMotivoCierre() {
  motivoPendiente = null
}

const CODIGOS_USUARIO_NO_HABILITADO = ['usuario_inactivo', 'usuario_no_registrado']

function manejarError(error: unknown) {
  if (!(error instanceof ApiError)) return
  if (error.status === 401) alExpirarSesion?.('sesion_expirada')
  else if (error.status === 403 && CODIGOS_USUARIO_NO_HABILITADO.includes(error.codigo)) {
    alExpirarSesion?.('usuario_inactivo')
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