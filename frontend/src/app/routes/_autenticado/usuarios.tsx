import { createFileRoute } from '@tanstack/react-router'
import { UsuariosPantalla } from '../../../features/usuarios/UsuariosPantalla'

export const Route = createFileRoute('/_autenticado/usuarios')({
  component: UsuariosPantalla,
})
