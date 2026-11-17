import { createFileRoute } from '@tanstack/react-router'
import { RepartoPantalla } from '../../../features/reparto/RepartoPantalla'

export const Route = createFileRoute('/_autenticado/reparto')({
  component: RepartoPantalla,
})
