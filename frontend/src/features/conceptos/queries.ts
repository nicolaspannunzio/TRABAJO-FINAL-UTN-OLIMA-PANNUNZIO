import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../services/api'
import type { Concepto, ConceptoActualizar, ConceptoCrear } from './tipos'

export const conceptosKeys = {
  lista: ['conceptos'] as const,
}

const json = (datos: unknown) => JSON.stringify(datos)

// --- Catálogo de conceptos (HU-05) -------------------------------------------------

export function useConceptos() {
  return useQuery({
    queryKey: conceptosKeys.lista,
    queryFn: () => apiFetch<Concepto[]>('/conceptos'),
  })
}

export function useCrearConcepto() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (datos: ConceptoCrear) =>
      apiFetch<Concepto>('/conceptos', { method: 'POST', body: json(datos) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: conceptosKeys.lista }),
  })
}

export function useActualizarConcepto() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, datos }: { id: string; datos: ConceptoActualizar }) =>
      apiFetch<Concepto>(`/conceptos/${id}`, { method: 'PATCH', body: json(datos) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: conceptosKeys.lista }),
  })
}