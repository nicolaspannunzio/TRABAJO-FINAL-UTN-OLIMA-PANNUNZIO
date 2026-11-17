import { createFileRoute } from '@tanstack/react-router'
import { PropiedadesPantalla } from '../../../features/propiedades/PropiedadesPantalla'

export const Route = createFileRoute('/_autenticado/propiedades')({
  component: PropiedadesPantalla,
})