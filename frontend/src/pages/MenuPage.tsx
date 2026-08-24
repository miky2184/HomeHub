import { ChefHat } from 'lucide-react'
import { useMenuWeek } from '../api/hooks'
import { Card } from '../components/Card'
import { DAY_LABELS, currentWeekStart } from '../lib/date'

function Row({ label, value }: { label: string; value: string | null }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, padding: '4px 0' }}>
      <span style={{ fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>{label}</span>
      <span style={{ fontSize: 'var(--fs-body)', textAlign: 'right' }}>{value ?? '—'}</span>
    </div>
  )
}

export function MenuPage() {
  const weekStart = currentWeekStart()
  const { data: week, isLoading, isError } = useMenuWeek(weekStart)

  if (isLoading) return <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>
  if (isError || !week) {
    return (
      <p style={{ color: 'var(--danger)' }}>
        Impossibile caricare il menu (richiede il Postgres configurato in backend/.env).
      </p>
    )
  }

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Cucina — menu della settimana</h1>
      <p style={{ fontSize: 'var(--fs-label)', color: 'var(--text-muted)', margin: '0 0 8px' }}>
        Sola lettura: il menu scuola/merende si aggiorna da Impostazioni (cambia solo un paio di volte l'anno).
      </p>

      {week.days.slice(0, 5).map((day) => (
        <Card key={day.day_of_week} label={DAY_LABELS[day.day_of_week]} icon={ChefHat} category="cucina">
          <Row label="Pranzo scuola" value={day.school_meal} />
          <Row label="Cena casa" value={day.home_meal} />
          <Row label="Merenda mattina" value={day.snack_morning} />
          <Row label="Merenda pomeriggio" value={day.snack_afternoon} />
        </Card>
      ))}
    </>
  )
}
