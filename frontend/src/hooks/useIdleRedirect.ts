import { useEffect, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

const IDLE_TIMEOUT_MS = 5 * 60_000
const ACTIVITY_EVENTS = ['pointerdown', 'pointermove', 'wheel', 'keydown'] as const

/** Dopo un periodo di inattività, riporta la dashboard alla Home
 * (vedi ARCHITECTURE.md §4.2 — idle/attract mode). */
export function useIdleRedirect() {
  const navigate = useNavigate()
  const location = useLocation()
  const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  useEffect(() => {
    function resetTimer() {
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => {
        if (location.pathname !== '/') navigate('/')
      }, IDLE_TIMEOUT_MS)
    }

    resetTimer()
    ACTIVITY_EVENTS.forEach((event) => window.addEventListener(event, resetTimer))

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
      ACTIVITY_EVENTS.forEach((event) => window.removeEventListener(event, resetTimer))
    }
  }, [location.pathname, navigate])
}
