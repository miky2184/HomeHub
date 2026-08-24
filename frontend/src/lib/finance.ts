import type { FinanceCategoryStatus } from '../api/types'

// MAI un valore in euro qui dentro — solo colori/etichette per le
// percentuali già calcolate dal backend (vedi api/types.ts).
export const ALERT_COLOR: Record<FinanceCategoryStatus['alert_level'], string> = {
  0: 'var(--accent)',
  1: 'var(--warning)',
  2: 'var(--danger)',
}

export const ALERT_LABEL: Record<FinanceCategoryStatus['alert_level'], string> = {
  0: 'In linea',
  1: 'Attenzione',
  2: 'Sopra budget',
}
