import { useEffect, useRef } from 'react'

/** Contatore globale (non uno stato React: nessun componente deve
 * ri-renderizzare quando cambia, lo legge solo useIdleRedirect al momento
 * dello scadere del timer) di quante sezioni della UI hanno in questo
 * momento modifiche non salvate. Un contatore invece di un booleano perché
 * più pagine/sezioni possono essere "dirty" insieme (es. due tab diversi
 * di Impostazioni se mai restassero montati insieme). */
let dirtyCount = 0

export function hasUnsavedChanges(): boolean {
  return dirtyCount > 0
}

/** Segnala a useIdleRedirect che questo componente ha in questo momento
 * modifiche non salvate (un form parzialmente compilato, una modale di
 * modifica aperta…) — il redirect automatico alla Home dopo inattività si
 * ferma finché isDirty resta true, invece di far perdere silenziosamente
 * quello che si stava scrivendo (es. il template menu scuola, un'attività
 * di Manutenzione appena iniziata, le credenziali di un'integrazione).
 * Va chiamato ad ogni render con lo stato "dirty" corrente, tipicamente
 * `value !== valoreOriginale` o `modaleAperta !== null`. */
export function useUnsavedChanges(isDirty: boolean): void {
  const wasDirty = useRef(false)

  useEffect(() => {
    if (isDirty && !wasDirty.current) {
      dirtyCount += 1
      wasDirty.current = true
    } else if (!isDirty && wasDirty.current) {
      dirtyCount -= 1
      wasDirty.current = false
    }
  }, [isDirty])

  // Smontaggio (cambio pagina, cambio tab in Impostazioni): non lasciare il
  // contatore incrementato per sempre se il componente sparisce mentre è
  // ancora "dirty" (es. si cambia tab senza salvare).
  useEffect(
    () => () => {
      if (wasDirty.current) {
        dirtyCount -= 1
        wasDirty.current = false
      }
    },
    []
  )
}
