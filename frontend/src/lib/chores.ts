import { toDateKey } from './date'

function formatShortDate(dateKey: string): string {
  const [, m, d] = dateKey.split('-')
  return `${d}/${m}`
}

/** Etichetta + flag "urgente" (scaduta, da fare oggi, o mai fatta: in
 * evidenza) per un'attività di manutenzione, confrontata con oggi in
 * locale — stesso approccio di lib/todo.ts:dueDateInfo, ma qui la data è
 * sempre presente (next_due_date è calcolata dal backend, mai null: vedi
 * aggregator.chore_item_out), quindi niente caso "nessuna scadenza". */
export function choreDueInfo(chore: { last_done_date: string | null; next_due_date: string }): {
  label: string
  overdue: boolean
} {
  if (!chore.last_done_date) return { label: 'Mai fatta', overdue: true }

  const today = toDateKey(new Date())
  const diffDays = Math.round(
    (new Date(`${chore.next_due_date}T00:00:00`).getTime() - new Date(`${today}T00:00:00`).getTime()) / 86_400_000
  )
  if (diffDays < 0) return { label: `In ritardo di ${Math.abs(diffDays)} gg`, overdue: true }
  if (diffDays === 0) return { label: 'Da fare oggi', overdue: true }
  if (diffDays === 1) return { label: 'Domani', overdue: false }
  return { label: `Tra ${diffDays} gg (${formatShortDate(chore.next_due_date)})`, overdue: false }
}

/** Testo per "ogni N giorni", con qualche caso comune più leggibile. */
export function intervalLabel(days: number): string {
  if (days === 7) return 'ogni settimana'
  if (days === 14) return 'ogni 2 settimane'
  if (days === 30) return 'ogni mese'
  if (days === 90) return 'ogni 3 mesi'
  if (days === 180) return 'ogni 6 mesi'
  if (days === 365) return 'ogni anno'
  return `ogni ${days} giorni`
}
