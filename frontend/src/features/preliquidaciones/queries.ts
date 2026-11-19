import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../services/api'
import type { PreliquidacionCrear, PreliquidacionOut, PreliquidacionResumen } from './tipos'

export const preliquidacionesKeys = {
  todas: ['preliquidaciones'] as const,
  periodo: (propiedadId: string, periodo: string) => ['preliquidaciones', propiedadId, periodo] as const,
  version: (id: string) => ['preliquidaciones', 'version', id] as const,
}

/** HU-12: cabeceras de todas las versiones del período, de la 1 en adelante. */
export function useVersiones(propiedadId: string, periodo: string) {
  return useQuery({
    queryKey: preliquidacionesKeys.periodo(propiedadId, periodo),
    queryFn: () => {
      const params = new URLSearchParams({ propiedad_id: propiedadId, periodo })
      return apiFetch<PreliquidacionResumen[]>(`/preliquidaciones?${params}`)
    },
  })
}

/** HU-12: una versión completa. Es inmutable, así que una vez leída no se vuelve a pedir. */
export function useVersion(id: string) {
  return useQuery({
    queryKey: preliquidacionesKeys.version(id),
    queryFn: () => apiFetch<PreliquidacionOut>(`/preliquidaciones/${id}`),
    staleTime: Infinity,
  })
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
