import { createFileRoute } from '@tanstack/react-router'
import { PreliquidacionesPantalla } from '../../../features/preliquidaciones/PreliquidacionesPantalla'

export const Route = createFileRoute('/_autenticado/preliquidaciones')({
  component: PreliquidacionesPantalla,
})
