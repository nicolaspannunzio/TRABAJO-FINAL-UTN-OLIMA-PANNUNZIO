import { ApiError } from '../../services/api'

// El texto se elige según `codigo`, nunca según el mensaje del backend.
export function textoError(error: unknown, accion: string): string {
  if (error instanceof ApiError) {
    switch (error.codigo) {
      case 'concepto_duplicado':
        return 'Ya existe un concepto con ese nombre.'
      case 'concepto_no_encontrado':
        return 'El concepto ya no existe. Recargá la lista.'
      case 'validacion':
        return 'Revisá los datos: alguno no es válido.'
      case 'sin_conexion':
        return 'No se pudo conectar con el servidor.'
    }
  }
  return `No se pudo ${accion}.`
}