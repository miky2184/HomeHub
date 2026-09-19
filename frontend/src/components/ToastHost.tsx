import { useSyncExternalStore } from 'react'
import { Check, X } from 'lucide-react'
import { dismissToast, getToasts, subscribeToasts } from '../lib/toast'

/** Montato una volta in AppLayout: mostra le conferme (o gli errori) di
 * salvataggio accodate con lib/toast.showToast, in basso al centro sopra a
 * tutto il resto. Un tap su un toast lo chiude subito, senza aspettare i 3s. */
export function ToastHost() {
  const toasts = useSyncExternalStore(subscribeToasts, getToasts, getToasts)
  if (toasts.length === 0) return null

  return (
    <div
      style={{
        position: 'fixed',
        left: '50%',
        bottom: 28,
        transform: 'translateX(-50%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 8,
        zIndex: 1000,
        pointerEvents: 'none',
      }}
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="status"
          onClick={() => dismissToast(toast.id)}
          style={{
            pointerEvents: 'auto',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '12px 20px',
            borderRadius: 'var(--radius-control)',
            background: toast.variant === 'error' ? 'var(--danger)' : 'var(--accent)',
            color: '#ffffff',
            fontSize: 'var(--fs-body)',
            fontWeight: 600,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.18)',
            animation: 'toast-in 0.2s ease-out',
          }}
        >
          {toast.variant === 'error' ? <X size={18} /> : <Check size={18} />}
          {toast.message}
        </div>
      ))}
    </div>
  )
}
