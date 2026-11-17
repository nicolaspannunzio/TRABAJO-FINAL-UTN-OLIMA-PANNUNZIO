import { createFileRoute, redirect } from '@tanstack/react-router'
import { LoginPantalla } from '../../features/auth/LoginPantalla'

export const Route = createFileRoute('/login')({
  beforeLoad: ({ context }) => {
    if (context.session) throw redirect({ to: '/' })
  },
  component: LoginPantalla,
})