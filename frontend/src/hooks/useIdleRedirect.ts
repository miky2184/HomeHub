import { useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { hasUnsavedChanges } from './useUnsavedChanges'

const IDLE_TIMEOUT_MS = 5 * 60_000
const ACTIVITY_EVENTS = ['pointerdown', 'pointermove', 'wheel', 'keydown'] as const

/** Dopo un periodo di inattività, riporta la dashboard alla Home
 * (vedi ARCHITECTURE.md §4.2 — idle/attract mode). Se però c'è un form a
 * metà (vedi useUnsavedChanges — template menu scuola, nuova attività di
 * Manutenzione, credenziali di un'integrazione…) il redirect non scatta:
 * si limita a riprovare più tardi, invece di far perdere quello che si
 * stava scrivendo solo perché ci si è allontanati per un attimo. */
export function useIdleRedirect() {
  const navigate = useNavigate()
  const location = useLocation()
  const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  useEffect(() => {
    function resetTimer() {
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(checkIdle, IDLE_TIMEOUT_MS)
    }

    function checkIdle() {
      if (location.pathname !== '/' && !hasUnsavedChanges()) {
        navigate('/')
      } else {
        resetTimer()
      }
    }

    resetTimer()
    ACTIVITY_EVENTS.forEach((event) => window.addEventListener(event, resetTimer))

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
      ACTIVITY_EVENTS.forEach((event) => window.removeEventListener(event, resetTimer))
    }
  }, [location.pathname, navigate])
}
