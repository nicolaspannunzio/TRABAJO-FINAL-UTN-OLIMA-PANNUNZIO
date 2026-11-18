import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError, apiFetch } from '../../services/api'
import type { ChecklistAbrir, ChecklistOut, FilaChecklist, NoCorrespondeOut, PropiedadOpcion } from './tipos'

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

/** HU-09: marca una fila como no corresponde. Si estaba cargada, el backend borra su importe. */
export function useMarcarNoCorresponde(propiedadId: string, periodo: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (filaId: string) =>
      apiFetch<NoCorrespondeOut>(`/checklist/${filaId}/no-corresponde`, { method: 'POST' }),
    onSuccess: (resp) => {
      // Solo los campos de la fila: estado_anterior e importe_eliminado no se guardan en la caché.
      const fila: FilaChecklist = {
        id: resp.id,
        concepto_propiedad_id: resp.concepto_propiedad_id,
        concepto: resp.concepto,
        estado: resp.estado,
        importe_id: resp.importe_id,
        importe: resp.importe,
      }
      qc.setQueryData<ChecklistOut | null>(checklistKeys.detalle(propiedadId, periodo), (prev) =>
        prev ? { ...prev, filas: prev.filas.map((f) => (f.id === fila.id ? fila : f)) } : prev,
      )
    },
  })
}
