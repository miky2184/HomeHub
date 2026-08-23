export const DAY_LABELS = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']

/** Lunedì della settimana corrente, in formato YYYY-MM-DD (coerente col backend). */
export function currentWeekStart(): string {
  const now = new Date()
  const day = (now.getDay() + 6) % 7 // 0 = lunedì
  const monday = new Date(now)
  monday.setDate(now.getDate() - day)
  return monday.toISOString().slice(0, 10)
}

export function todayDayOfWeek(): number {
  return (new Date().getDay() + 6) % 7
}
