import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../../services/api'
import type { UsuarioActualizar, UsuarioCrear, UsuarioOut } from './tipos'

export const usuariosKeys = {
  todos: ['usuarios'] as const,
}

export function useUsuarios() {
  return useQuery({
    queryKey: usuariosKeys.todos,
    queryFn: () => apiFetch<UsuarioOut[]>('/usuarios'),
    // Un 403 (el usuario no es admin) no se arregla reintentando.
    retry: false,
  })
}

// Después de cada escritura se invalida la lista: la pantalla no guarda copias de los datos.

/** HU-02: alta. El backend crea la cuenta en Supabase Auth y la fila en `usuario`. */
export function useCrearUsuario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (datos: UsuarioCrear) =>
      apiFetch<UsuarioOut>('/usuarios', { method: 'POST', body: JSON.stringify(datos) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: usuariosKeys.todos }),
  })
}

export function useActualizarUsuario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, datos }: { id: string; datos: UsuarioActualizar }) =>
      apiFetch<UsuarioOut>(`/usuarios/${id}`, { method: 'PATCH', body: JSON.stringify(datos) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: usuariosKeys.todos }),
  })
}

/** Baja lógica: el usuario queda inactivo, no se borra. */
export function useDarDeBaja() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiFetch<UsuarioOut>(`/usuarios/${id}/baja`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: usuariosKeys.todos }),
  })
}
