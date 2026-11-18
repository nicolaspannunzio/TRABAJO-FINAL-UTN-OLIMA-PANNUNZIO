import { useEffect, useState, type FormEvent } from 'react'
import { useSession } from '../../context/session'
import { queryClient, leerMotivoCierre, limpiarMotivoCierre } from '../../app/queryClient'

const AVISOS = {
  sesion_expirada: 'Tu sesión expiró. Ingresá de nuevo.',
  usuario_inactivo: 'Tu usuario está inactivo o no está habilitado. Consultá con un administrador.',
}

export function LoginPantalla() {
  const { iniciarSesion } = useSession()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [aviso] = useState(() => leerMotivoCierre())

  // Acá no hay pantallas con datos montadas: es el momento seguro de vaciar el caché
  // (evita mostrar datos de la sesión anterior).
  useEffect(() => {
    queryClient.clear()
    limpiarMotivoCierre()
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
      {aviso && !error && <p role="status">{AVISOS[aviso]}</p>}
      {error && <p role="alert">{error}</p>}
      <button type="submit" disabled={enviando}>
        {enviando ? 'Ingresando…' : 'Ingresar'}
      </button>
    </form>
  )
}