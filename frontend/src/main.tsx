import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { App } from './app/App'
import { queryClient, registrarAlExpirarSesion } from './app/queryClient'
import { SessionProvider } from './context/SessionProvider'
import { supabase } from './services/supabase'

// 401 desde cualquier query o mutación: si había sesión, se cierra.
// El cambio de sesión hace que la guarda del Router redirija al login.
registrarAlExpirarSesion(async () => {
  const { data } = await supabase.auth.getSession()
  if (data.session) await supabase.auth.signOut()
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <SessionProvider>
        <App />
      </SessionProvider>
    </QueryClientProvider>
  </StrictMode>,
)