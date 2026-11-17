import { createFileRoute } from '@tanstack/react-router'
import { ConceptosPantalla } from '../../../features/conceptos/ConceptosPantalla'

export const Route = createFileRoute('/_autenticado/conceptos')({
  component: ConceptosPantalla,
})
