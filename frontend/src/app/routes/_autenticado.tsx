import { createFileRoute, redirect } from '@tanstack/react-router'
import { Layout } from '../../components/Layout'

export const Route = createFileRoute('/_autenticado')({
  beforeLoad: ({ context }) => {
    if (!context.session) throw redirect({ to: '/login' })
  },
  component: Layout,
})