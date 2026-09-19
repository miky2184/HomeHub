/** Toast globali (conferma "salvato", errori di salvataggio) — store minimale
 * fuori da React, sullo stesso principio del contatore in
 * hooks/useUnsavedChanges.ts: nessun Context/Provider da innestare, un solo
 * <ToastHost/> (montato una volta in layout/AppLayout.tsx) legge lo stato
 * corrente con useSyncExternalStore e si aggiorna quando cambia.
 *
 * Usato per ora solo dalle mutation di Impostazioni (vedi api/hooks.ts) —
 * niente a che fare con azioni "leggere" e frequenti come spuntare un
 * prodotto della spesa, dove un toast ad ogni click sarebbe solo rumore. */

export interface Toast {
  id: number
  message: string
  variant: 'success' | 'error'
}

const TOAST_DURATION_MS = 3000

let toasts: Toast[] = []
let nextId = 0
const listeners = new Set<() => void>()

function emit(): void {
  listeners.forEach((listener) => listener())
}

export function subscribeToasts(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function getToasts(): Toast[] {
  return toasts
}

export function showToast(message: string, variant: Toast['variant'] = 'success'): void {
  const id = nextId++
  toasts = [...toasts, { id, message, variant }]
  emit()
  setTimeout(() => dismissToast(id), TOAST_DURATION_MS)
}

export function dismissToast(id: number): void {
  toasts = toasts.filter((toast) => toast.id !== id)
  emit()
}
