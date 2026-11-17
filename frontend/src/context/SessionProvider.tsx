import { useEffect, useState, type ReactNode } from 'react'
import type { Session } from '@supabase/supabase-js'
import { supabase } from '../services/supabase'
import { SessionContext } from './session'

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      setCargando(false)
    })
    const { data } = supabase.auth.onAuthStateChange((_evento, nueva) => {
      setSession(nueva)
    })
    return () => data.subscription.unsubscribe()
  }, [])

  async function iniciarSesion(email: string, password: string) {
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
  }

  async function cerrarSesion() {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  }

  return (
    <SessionContext.Provider value={{ session, cargando, iniciarSesion, cerrarSesion }}>
      {children}
    </SessionContext.Provider>
  )
}