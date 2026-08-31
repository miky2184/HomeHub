// Palette per categoria: badge icona nelle card + stato attivo nel rail
// (vedi variabili --cat-*-bg/--cat-*-fg in styles/theme.css).

export type Category =
  | 'home'
  | 'agenda'
  | 'scuola'
  | 'cucina'
  | 'attivita'
  | 'spesa'
  | 'casa'
  | 'evidenza'
  | 'todo'
  | 'manutenzione'
  | 'spedizioni'

export const CATEGORY_COLORS: Record<Category, { bg: string; fg: string }> = {
  home: { bg: 'var(--cat-home-bg)', fg: 'var(--cat-home-fg)' },
  agenda: { bg: 'var(--cat-agenda-bg)', fg: 'var(--cat-agenda-fg)' },
  scuola: { bg: 'var(--cat-agenda-bg)', fg: 'var(--cat-agenda-fg)' },
  cucina: { bg: 'var(--cat-cucina-bg)', fg: 'var(--cat-cucina-fg)' },
  attivita: { bg: 'var(--cat-attivita-bg)', fg: 'var(--cat-attivita-fg)' },
  spesa: { bg: 'var(--cat-spesa-bg)', fg: 'var(--cat-spesa-fg)' },
  casa: { bg: 'var(--cat-casa-bg)', fg: 'var(--cat-casa-fg)' },
  evidenza: { bg: 'var(--cat-evidenza-bg)', fg: 'var(--cat-evidenza-fg)' },
  todo: { bg: 'var(--cat-todo-bg)', fg: 'var(--cat-todo-fg)' },
  manutenzione: { bg: 'var(--cat-manutenzione-bg)', fg: 'var(--cat-manutenzione-fg)' },
  spedizioni: { bg: 'var(--cat-spedizioni-bg)', fg: 'var(--cat-spedizioni-fg)' },
}
