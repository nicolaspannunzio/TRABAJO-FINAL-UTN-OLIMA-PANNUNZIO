import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError, apiFetch } from '../../services/api'
import type { ChecklistAbrir, ChecklistOut, PropiedadOpcion } from './tipos'

export const checklistKeys = {
  todos: ['checklist'] as const,
  // Clave propia: el selector no depende de las queries del módulo propiedades (A).
  propiedades: ['checklist', 'propiedades'] as const,
  detalle: (propiedadId: string, periodo: string) => ['checklist', propiedadId, periodo] as const,
}

export function usePropiedadesOpciones() {
  return useQuery({
    queryKey: checklistKeys.propiedades,
    queryFn: () => apiFetch<PropiedadOpcion[]>('/propiedades'),
  })
}

/** Checklist del período. `null` significa "período todavía no abierto" (404 del GET). */
export function useChecklist(propiedadId: string, periodo: string) {
  return useQuery({
    queryKey: checklistKeys.detalle(propiedadId, periodo),
    queryFn: async (): Promise<ChecklistOut | null> => {
      const params = new URLSearchParams({ propiedad_id: propiedadId, periodo })
      try {
        return await apiFetch<ChecklistOut>(`/checklist?${params}`)
      } catch (e) {
        if (e instanceof ApiError && e.codigo === 'checklist_no_encontrado') return null
        throw e
      }
    },
  })
}

/** HU-07: abre el período. Es idempotente: si ya estaba abierto, devuelve el existente. */
export function useAbrirPeriodo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (datos: ChecklistAbrir) =>
      apiFetch<ChecklistOut>('/checklist', { method: 'POST', body: JSON.stringify(datos) }),
    onSuccess: (checklist) => {
      qc.setQueryData(checklistKeys.detalle(checklist.propiedad_id, checklist.periodo), checklist)
    },
  })
}