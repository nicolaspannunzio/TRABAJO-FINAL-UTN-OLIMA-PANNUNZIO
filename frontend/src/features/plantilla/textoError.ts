import { ApiError } from '../../services/api'

// El texto se elige según `codigo`, nunca según el mensaje del backend.
export function textoError(error: unknown, accion: string): string {
  if (error instanceof ApiError) {
    switch (error.codigo) {
      case 'concepto_ya_asociado':
        return 'Ese concepto ya está en la plantilla de la propiedad. Si está inactivo, activalo desde la lista.'
      case 'propiedad_no_encontrada':
        return 'La propiedad ya no existe. Recargá la lista.'
      case 'concepto_no_encontrado':
        return 'El concepto ya no existe. Recargá la lista.'
      case 'concepto_propiedad_no_encontrado':
        return 'Ese concepto ya no está en la plantilla. Recargá la lista.'
      case 'validacion':
        return 'Revisá los datos: alguno no es válido.'
      case 'sin_conexion':
        return 'No se pudo conectar con el servidor.'
    }
  }
  return `No se pudo ${accion}.`
}