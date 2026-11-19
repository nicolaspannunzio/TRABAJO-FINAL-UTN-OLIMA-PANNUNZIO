import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../services/api'
import type { ConceptoPropiedad } from './tipos'

export const plantillaKeys = {
  de: (propiedadId: string) => ['propiedades', propiedadId, 'conceptos'] as const,
}

const json = (datos: unknown) => JSON.stringify(datos)

// --- Plantilla de conceptos por propiedad (HU-06) ---------------------------------------

export function usePlantilla(propiedadId: string) {
  return useQuery({
    queryKey: plantillaKeys.de(propiedadId),
    queryFn: () => apiFetch<ConceptoPropiedad[]>(`/propiedades/${propiedadId}/conceptos`),
  })
}

export function useAsociarConcepto(propiedadId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (conceptoId: string) =>
      apiFetch<ConceptoPropiedad>(`/propiedades/${propiedadId}/conceptos`, {
        method: 'POST',
        body: json({ concepto_id: conceptoId }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: plantillaKeys.de(propiedadId) }),
  })
}

export function useCambiarActivo(propiedadId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, activo }: { id: string; activo: boolean }) =>
      apiFetch<ConceptoPropiedad>(`/propiedades/${propiedadId}/conceptos/${id}`, {
        method: 'PATCH',
        body: json({ activo }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: plantillaKeys.de(propiedadId) }),
  })
}