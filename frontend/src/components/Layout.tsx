import { Link, Outlet } from '@tanstack/react-router'
import { useSession } from '../context/session'
import { NAVEGACION } from '../app/navegacion'

export function Layout() {
  const { session, cerrarSesion } = useSession()

  return (
    <div>
      <header style={{ display: 'flex', gap: '1rem', alignItems: 'center', padding: '0.75rem 1rem', borderBottom: '1px solid #ccc' }}>
        <nav style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', flex: 1 }}>
          {NAVEGACION.map((item) => (
            <Link key={item.to} to={item.to} activeProps={{ style: { fontWeight: 'bold' } }}>
              {item.etiqueta}
            </Link>
          ))}
        </nav>
        <span>{session?.user.email}</span>
        <button onClick={() => void cerrarSesion()}>Cerrar sesión</button>
      </header>
      <main style={{ padding: '1rem' }}>
        <Outlet />
      </main>
    </div>
  )
}