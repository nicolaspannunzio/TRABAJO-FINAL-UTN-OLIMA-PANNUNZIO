import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ApiError, apiFetch } from '../../services/api'
// checklist e importes son los dos de B: se comparten las query keys y los tipos.
import { checklistKeys } from '../checklist/queries'
import type { ChecklistOut, FilaChecklist } from '../checklist/tipos'
import type { ImporteCrear } from './tipos'

/** HU-08: carga un importe. Devuelve la fila del checklist ya en `cargado`. */
export function useCargarImporte() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (datos: ImporteCrear) =>
      apiFetch<FilaChecklist>('/importes', { method: 'POST', body: JSON.stringify(datos) }),
    onSuccess: (fila, datos) => {
      // Reemplaza solo la fila cargada en el checklist que ya está en caché.
      qc.setQueryData<ChecklistOut | null>(
        checklistKeys.detalle(datos.propiedad_id, datos.periodo),
        (prev) => (prev ? { ...prev, filas: prev.filas.map((f) => (f.id === fila.id ? fila : f)) } : prev),
      )
    },
    onError: (error, datos) => {
      // Duplicado: otro usuario (u otra pestaña) cargó primero. Se refresca para mostrar ese importe.
      if (error instanceof ApiError && error.codigo === 'importe_duplicado') {
        void qc.invalidateQueries({ queryKey: checklistKeys.detalle(datos.propiedad_id, datos.periodo) })
      }
    },
  })
}
