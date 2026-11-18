import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../services/api'
import type { AdvertenciaPrevia } from './tipos'

export const advertenciasKeys = {
  todas: ['advertencias'] as const,
  // `version` resume el estado del checklist: si cambia un importe o un estado,
  // cambia la clave y la vista previa se vuelve a pedir sola.
  periodo: (propiedadId: string, periodo: string, version: string) =>
    ['advertencias', propiedadId, periodo, version] as const,
}

/** HU-10: vista previa de advertencias del período. No persiste ni bloquea. */
export function useAdvertencias(propiedadId: string, periodo: string, version: string) {
  return useQuery({
    queryKey: advertenciasKeys.periodo(propiedadId, periodo, version),
    queryFn: () => {
      const params = new URLSearchParams({ propiedad_id: propiedadId, periodo })
      return apiFetch<AdvertenciaPrevia[]>(`/advertencias?${params}`)
    },
    // Mientras se recalcula, se sigue mostrando la lista anterior (sin parpadeo).
    placeholderData: keepPreviousData,
  })
}
