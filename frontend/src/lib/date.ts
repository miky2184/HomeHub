export const DAY_LABELS = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']

/** Lunedì della settimana corrente, in formato YYYY-MM-DD (coerente col
 * backend). toDateKey (sotto), non toISOString: quest'ultima converte in
 * UTC, e tra le 00:00 e le ~02:00 locali (Italia, UTC+2 in estate) darebbe
 * la data di ieri — un lunedì diventerebbe domenica, sbagliando la
 * settimana per Allenamenti/Menu proprio nelle prime ore del giorno. */
export function currentWeekStart(): string {
  const now = new Date()
  const day = (now.getDay() + 6) % 7 // 0 = lunedì
  const monday = new Date(now)
  monday.setDate(now.getDate() - day)
  return toDateKey(monday)
}

export function todayDayOfWeek(): number {
  return (new Date().getDay() + 6) % 7
}

export function isSameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
}

/** Chiave locale YYYY-MM-DD (niente conversione UTC: evita che un evento
 * vicino a mezzanotte finisca nel giorno sbagliato per via del fuso). */
export function toDateKey(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/** "YYYY-MM-DD" -> "DD/MM", per le etichette brevi di scadenza/data (Todo,
 * Manutenzione, Home Inventory — prima era ridefinita identica in ognuno
 * di questi file). */
export function formatShortDate(dateKey: string): string {
  const [, m, d] = dateKey.split('-')
  return `${d}/${m}`
}

/** Data di un giorno del piano allenamenti, dato lunedì della settimana
 * (YYYY-MM-DD, formato backend) e l'indice 0=lunedì...6=domenica. */
export function dateFromWeek(weekStartDate: string, dayOfWeek: number): Date {
  const [y, m, d] = weekStartDate.split('-').map(Number)
  const date = new Date(y, m - 1, d)
  date.setDate(date.getDate() + dayOfWeek)
  return date
}

/** Etichetta leggibile per una data vicina: "Oggi" | "Domani" | "Lunedì 3/9"
 * (get_next_training garantisce sempre oggi o un giorno futuro, mai
 * passato, quindi niente caso "scaduto" da gestire qui). */
export function relativeDayLabel(date: Date): string {
  const today = new Date()
  if (isSameDay(date, today)) return 'Oggi'
  const tomorrow = new Date(today)
  tomorrow.setDate(today.getDate() + 1)
  if (isSameDay(date, tomorrow)) return 'Domani'
  return `${DAY_LABELS[(date.getDay() + 6) % 7]} ${date.getDate()}/${date.getMonth() + 1}`
}

/** I 7 giorni (lunedì-domenica) della settimana che contiene referenceDate. */
export function getWeekDates(referenceDate: Date): Date[] {
  const day = (referenceDate.getDay() + 6) % 7
  const monday = new Date(referenceDate)
  monday.setHours(0, 0, 0, 0)
  monday.setDate(referenceDate.getDate() - day)
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i)
    return d
  })
}

/** Griglia del mese (year, month 0-indexed) come settimane lunedì-domenica
 * complete, incluse le code del mese precedente/successivo. */
export function getMonthGrid(year: number, month: number): Date[][] {
  const firstOfMonth = new Date(year, month, 1)
  const firstWeekday = (firstOfMonth.getDay() + 6) % 7
  const gridStart = new Date(year, month, 1 - firstWeekday)

  const lastOfMonth = new Date(year, month + 1, 0)
  const lastWeekday = (lastOfMonth.getDay() + 6) % 7
  const gridEnd = new Date(year, month, lastOfMonth.getDate() + (6 - lastWeekday))

  const weeks: Date[][] = []
  let cursor = new Date(gridStart)
  while (cursor <= gridEnd) {
    const week = Array.from({ length: 7 }, (_, i) => {
      const d = new Date(cursor)
      d.setDate(cursor.getDate() + i)
      return d
    })
    weeks.push(week)
    cursor = new Date(cursor)
    cursor.setDate(cursor.getDate() + 7)
  }
  return weeks
}
