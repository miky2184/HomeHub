// TODO: rendere configurabile da una pagina Impostazioni invece di un valore fisso.
export const FAMILY_MEMBER_NAME = 'Michele'

export function getGreeting(date: Date = new Date()): string {
  const hour = date.getHours()
  if (hour < 12) return 'Buongiorno'
  if (hour < 18) return 'Buon pomeriggio'
  return 'Buonasera'
}
