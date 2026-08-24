export function getGreeting(date: Date = new Date()): string {
  const hour = date.getHours()
  if (hour < 12) return 'Buongiorno 🌞'
  if (hour < 18) return 'Buon pomeriggio 🌅'
  return 'Buonasera 🌛'
}
