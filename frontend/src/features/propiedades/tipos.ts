// Provisorio: en F0-08 estos tipos pasan a generarse desde docs/openapi.json.
export interface Propiedad {
  id: string
  direccion: string
  localidad: string | null
  estado: string
  fecha_alta: string
}