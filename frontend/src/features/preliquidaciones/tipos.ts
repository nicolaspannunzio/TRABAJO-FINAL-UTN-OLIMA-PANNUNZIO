// Tipos de preliquidaciones, tomados del contrato generado (docs/openapi.json → types/api.ts).
import type { components } from '../../types/api'

export type PreliquidacionCrear = components['schemas']['PreliquidacionCrear']
export type PreliquidacionOut = components['schemas']['PreliquidacionOut']
export type PreliquidacionResumen = components['schemas']['PreliquidacionResumen']
export type TipoAdvertencia = PreliquidacionOut['advertencias'][number]['tipo']

/** Un concepto pendiente, como viene en el detalle del 409 `pendientes_sin_confirmar`. */
export interface ConceptoPendiente {
  concepto_propiedad_id: string
  concepto: string
}
