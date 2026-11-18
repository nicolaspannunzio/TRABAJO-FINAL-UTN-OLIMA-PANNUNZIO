import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../services/api'
import type { PreliquidacionCrear, PreliquidacionOut } from './tipos'

export const preliquidacionesKeys = {
  todas: ['preliquidaciones'] as const,
  periodo: (propiedadId: string, periodo: string) => ['preliquidaciones', propiedadId, periodo] as const,
}

/** HU-11: genera la versión siguiente. Con pendientes y sin confirmar, el backend responde 409. */
export function useGenerarPreliquidacion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (datos: PreliquidacionCrear) =>
      apiFetch<PreliquidacionOut>('/preliquidaciones', { method: 'POST', body: JSON.stringify(datos) }),
    onSuccess: (_, datos) => {
      // El historial de versiones (HU-12) se vuelve a pedir cuando se muestre.
      void qc.invalidateQueries({ queryKey: preliquidacionesKeys.periodo(datos.propiedad_id, datos.periodo) })
    },
  })
}
