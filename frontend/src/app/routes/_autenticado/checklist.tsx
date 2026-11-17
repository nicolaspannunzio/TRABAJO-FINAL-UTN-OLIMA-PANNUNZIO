import { createFileRoute } from '@tanstack/react-router'
import { ChecklistPantalla } from '../../../features/checklist/ChecklistPantalla'

export const Route = createFileRoute('/_autenticado/checklist')({
  component: ChecklistPantalla,
})
