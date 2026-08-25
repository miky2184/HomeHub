import { useEffect, type ReactNode } from 'react'
import { useAuthStatus } from '../api/hooks'
import { LoginPage } from '../pages/LoginPage'

/** Mostra la Login al posto della dashboard finché non c'è un cookie di
 * sessione valido (vedi backend/app/core/auth.py) — se auth_required è
 * false (nessuna password ancora configurata in backend/.env) non blocca
 * mai nulla. Ascolta anche "homehub:unauthorized" (client.ts, un 401 da
 * qualunque richiesta) per rimostrare subito la Login se la sessione
 * scade mentre si sta usando l'app, senza aspettare il prossimo refetch
 * automatico. */
export function AuthGate({ children }: { children: ReactNode }) {
  const { data, isLoading, refetch } = useAuthStatus()

  useEffect(() => {
    function handleUnauthorized() {
      refetch()
    }
    window.addEventListener('homehub:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('homehub:unauthorized', handleUnauthorized)
  }, [refetch])

  if (isLoading) return null
  if (data?.auth_required && !data.authenticated) {
    return <LoginPage onSuccess={() => refetch()} />
  }
  return <>{children}</>
}
