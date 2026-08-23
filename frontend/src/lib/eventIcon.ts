import { CalendarDays, Dumbbell, Goal, Utensils } from 'lucide-react'
import type { ComponentType } from 'react'
import type { Category } from '../styles/categories'

interface EventIconMatch {
  Icon: ComponentType<{ size?: number }>
  category: Category
}

const RULES: Array<{ keywords: string[]; match: EventIconMatch }> = [
  { keywords: ['pranzo', 'cena', 'colazione'], match: { Icon: Utensils, category: 'cucina' } },
  { keywords: ['corsa', 'allenamento', 'palestra', 'piscina'], match: { Icon: Dumbbell, category: 'attivita' } },
  { keywords: ['calcio', 'partita', 'tennis'], match: { Icon: Goal, category: 'attivita' } },
]

/** Euristica leggera solo per l'icona in Home: cerca parole chiave nel titolo
 * dell'evento. Nessun impatto sui dati, puramente visivo. */
export function inferEventIcon(title: string): EventIconMatch {
  const lower = title.toLowerCase()
  for (const rule of RULES) {
    if (rule.keywords.some((k) => lower.includes(k))) return rule.match
  }
  return { Icon: CalendarDays, category: 'agenda' }
}
