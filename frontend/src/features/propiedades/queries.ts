import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../services/api'
import type {
  Propiedad,
  PropiedadActualizar,
  PropiedadCrear,
  Propietario,
  PropietarioActualizar,
  PropietarioCrear,
} from './tipos'

export const propiedadesKeys = {
  lista: ['propiedades'] as const,
}

export const propietariosKeys = {
  lista: ['propietarios'] as const,
}

const json = (datos: unknown) => JSON.stringify(datos)

// --- Propiedades (HU-03) ---------------------------------------------------------

export function usePropiedades() {
  return useQuery({
    queryKey: propiedadesKeys.lista,
    queryFn: () => apiFetch<Propiedad[]>('/propiedades'),
  })
}

export function useCrearPropiedad() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (datos: PropiedadCrear) =>
      apiFetch<Propiedad>('/propiedades', { method: 'POST', body: json(datos) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: propiedadesKeys.lista }),
  })
}

export function useActualizarPropiedad() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, datos }: { id: string; datos: PropiedadActualizar }) =>
      apiFetch<Propiedad>(`/propiedades/${id}`, { method: 'PATCH', body: json(datos) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: propiedadesKeys.lista }),
  })
}

// --- Propietarios (HU-03) --------------------------------------------------------

export function usePropietarios() {
  return useQuery({
    queryKey: propietariosKeys.lista,
    queryFn: () => apiFetch<Propietario[]>('/propietarios'),
  })
}

export function useCrearPropietario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (datos: PropietarioCrear) =>
      apiFetch<Propietario>('/propietarios', { method: 'POST', body: json(datos) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: propietariosKeys.lista }),
  })
}

export function useActualizarPropietario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, datos }: { id: string; datos: PropietarioActualizar }) =>
      apiFetch<Propietario>(`/propietarios/${id}`, { method: 'PATCH', body: json(datos) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: propietariosKeys.lista }),
  })
}
