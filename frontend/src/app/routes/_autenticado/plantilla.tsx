import { createFileRoute } from '@tanstack/react-router'
import { PlantillaPantalla } from '../../../features/plantilla/PlantillaPantalla'

export const Route = createFileRoute('/_autenticado/plantilla')({
  component: PlantillaPantalla,
})
