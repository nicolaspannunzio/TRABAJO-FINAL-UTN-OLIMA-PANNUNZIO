import { useEffect, useState, type FormEvent } from 'react'
import { createFileRoute, redirect } from '@tanstack/react-router'
import { useSession } from '../../context/session'
import { queryClient } from '../queryClient'

export const Route = createFileRoute('/login')({
  beforeLoad: ({ context }) => {
    if (context.session) throw redirect({ to: '/' })
  },
  component: Login,
})

function Login() {
  const { iniciarSesion } = useSession()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  // Acá no hay pantallas con datos montadas: es el momento seguro de vaciar el caché
  // (evita mostrar datos de la sesión anterior).
  useEffect(() => {
    queryClient.clear()
  }, [])

  async function enviar(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      await iniciarSesion(email, password)
      // La redirección la hace la guarda al cambiar la sesión.
    } catch {
      setError('Email o contraseña incorrectos')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={enviar}>
      <h1>Iniciar sesión</h1>
      <label>
        Email
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </label>
      <label>
        Contraseña
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </label>
      {error && <p role="alert">{error}</p>}
      <button type="submit" disabled={enviando}>
        {enviando ? 'Ingresando…' : 'Ingresar'}
      </button>
    </form>
  )
}