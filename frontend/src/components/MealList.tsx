/** Un pasto scolastico è quasi sempre più portate, una per riga (es. "Pasta
 * integrale BIO al pomodoro" / "Polpette con soia in salsa curry" / ...).
 * Divide su a capo e mostra ogni riga con un pallino, invece di un unico
 * blocco di testo — funziona sia se il testo inserito ha già un proprio
 * punto elenco ("·", "-", "*") sia se no (viene rimosso e sostituito con
 * quello stilizzato, per coerenza visiva). */

const BULLET_PREFIX = /^[·\-*•]\s*/

function parseMealLines(text: string): string[] {
  return text
    .split('\n')
    .map((line) => line.replace(BULLET_PREFIX, '').trim())
    .filter(Boolean)
}

interface MealListProps {
  text: string
  color?: string
}

export function MealList({ text, color = 'var(--text-primary)' }: MealListProps) {
  const lines = parseMealLines(text)
  if (lines.length === 0) return null

  return (
    <div>
      {lines.map((line, i) => (
        <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', margin: i > 0 ? '4px 0 0' : 0 }}>
          <span aria-hidden style={{ color, lineHeight: 'var(--fs-body)' }}>
            ·
          </span>
          <span style={{ fontSize: 'var(--fs-body)', color }}>{line}</span>
        </div>
      ))}
    </div>
  )
}
