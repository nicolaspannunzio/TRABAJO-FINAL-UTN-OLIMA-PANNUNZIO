import { ApiError } from '../../services/api'

// El texto se elige según `codigo`, nunca según el mensaje del backend.
export function textoError(error: unknown, accion: string): string {
  if (error instanceof ApiError) {
    switch (error.codigo) {
      case 'propiedad_no_encontrada':
        return 'La propiedad ya no existe. Recargá la lista.'
      case 'propietario_no_encontrado':
        return 'El propietario ya no existe. Recargá la lista.'
      case 'validacion':
        return 'Revisá los datos: alguno no es válido.'
      case 'sin_conexion':
        return 'No se pudo conectar con el servidor.'
    }
  }
  return `No se pudo ${accion}.`
}
