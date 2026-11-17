import { createFileRoute } from '@tanstack/react-router'
import { AdvertenciasPantalla } from '../../../features/advertencias/AdvertenciasPantalla'

export const Route = createFileRoute('/_autenticado/advertencias')({
  component: AdvertenciasPantalla,
})
