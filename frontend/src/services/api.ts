import { supabase } from './supabase'

const BASE_URL = import.meta.env.VITE_API_URL

// Formato de error del backend: { codigo, mensaje, detalle }
export class ApiError extends Error {
  status: number
  codigo: string
  detalle: unknown

  constructor(status: number, codigo: string, mensaje: string, detalle: unknown = null) {
    super(mensaje)
    this.name = 'ApiError'
    this.status = status
    this.codigo = codigo
    this.detalle = detalle
  }
}

export async function apiFetch<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token

  const headers = new Headers(opciones.headers)
  headers.set('Accept', 'application/json')
  if (opciones.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let respuesta: Response
  try {
    respuesta = await fetch(`${BASE_URL}${ruta}`, { ...opciones, headers })
  } catch {
    throw new ApiError(0, 'sin_conexion', 'No se pudo conectar con el servidor')
  }

  if (!respuesta.ok) {
    let cuerpo: { codigo?: string; mensaje?: string; detalle?: unknown } | null = null
    try {
      cuerpo = await respuesta.json()
    } catch {
      // el cuerpo no era JSON: se usa el texto de estado
    }
    throw new ApiError(
      respuesta.status,
      cuerpo?.codigo ?? 'error_desconocido',
      cuerpo?.mensaje ?? respuesta.statusText,
      cuerpo?.detalle ?? null,
    )
  }

  if (respuesta.status === 204) return undefined as T
  return (await respuesta.json()) as T
}