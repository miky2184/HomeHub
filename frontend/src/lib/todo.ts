import type { TodoPriority } from '../api/types'
import { formatShortDate, toDateKey } from './date'

export const PRIORITY_META: Record<TodoPriority, { label: string; color: string }> = {
  alta: { label: 'Alta', color: 'var(--danger)' },
  media: { label: 'Media', color: 'var(--warning)' },
  bassa: { label: 'Bassa', color: 'var(--accent)' },
}

export const PRIORITY_OPTIONS: TodoPriority[] = ['alta', 'media', 'bassa']

/** Etichetta + flag "scaduto" per una scadenza, confrontata con oggi in
 * locale (niente conversione UTC, stesso approccio di lib/date.ts). */
export function dueDateInfo(dueDate: string | null): { label: string; overdue: boolean } | null {
  if (!dueDate) return null
  const today = toDateKey(new Date())
  if (dueDate === today) return { label: 'Oggi', overdue: false }

  const diffDays = Math.round(
    (new Date(`${dueDate}T00:00:00`).getTime() - new Date(`${today}T00:00:00`).getTime()) / 86_400_000
  )
  if (diffDays < 0) return { label: `Scaduto (${formatShortDate(dueDate)})`, overdue: true }
  if (diffDays === 1) return { label: 'Domani', overdue: false }
  return { label: `Entro il ${formatShortDate(dueDate)}`, overdue: false }
}
