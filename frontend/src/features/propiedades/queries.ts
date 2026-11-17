import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../services/api'
import type { Propiedad } from './tipos'

export const propiedadesKeys = {
  lista: ['propiedades'] as const,
}

export function usePropiedades() {
  return useQuery({
    queryKey: propiedadesKeys.lista,
    queryFn: () => apiFetch<Propiedad[]>('/propiedades'),
  })
}