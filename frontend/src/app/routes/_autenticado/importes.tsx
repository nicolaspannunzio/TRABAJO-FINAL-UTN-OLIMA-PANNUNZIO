import { createFileRoute } from '@tanstack/react-router'
import { ImportesPantalla } from '../../../features/importes/ImportesPantalla'

export const Route = createFileRoute('/_autenticado/importes')({
  component: ImportesPantalla,
})
