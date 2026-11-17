import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_autenticado/')({
  beforeLoad: () => {
    throw redirect({ to: '/propiedades' })
  },
})