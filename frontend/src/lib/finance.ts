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

/** Solo giorno/mese o "Oggi"/"Domani" — mai un importo, questa è la data di
 * una spesa in arrivo (vedi UpcomingExpense in api/types.ts). */
export function formatUpcomingDate(dueDate: string): string {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const target = new Date(`${dueDate}T00:00:00`)
  const diffDays = Math.round((target.getTime() - today.getTime()) / 86_400_000)
  if (diffDays === 0) return 'Oggi'
  if (diffDays === 1) return 'Domani'
  const [, m, d] = dueDate.split('-')
  return `${d}/${m}`
}
