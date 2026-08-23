import { useEffect, useState } from 'react'
import { ChefHat } from 'lucide-react'
import { useMenuWeek, useUpsertSchoolMenu } from '../api/hooks'
import { Card } from '../components/Card'
import { DAY_LABELS, currentWeekStart } from '../lib/date'
import { buttonStyle, inputStyle } from '../styles/controls'

export function MenuPage() {
  const weekStart = currentWeekStart()
  const { data: week, isLoading, isError } = useMenuWeek(weekStart)
  const upsertSchoolMenu = useUpsertSchoolMenu(weekStart)
  const [drafts, setDrafts] = useState<Record<number, string>>({})

  useEffect(() => {
    if (!week) return
    const next: Record<number, string> = {}
    week.days.forEach((d) => {
      next[d.day_of_week] = d.school_meal ?? ''
    })
    setDrafts(next)
  }, [week])

  if (isLoading) return <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>
  if (isError || !week) {
    return <p style={{ color: 'var(--danger)' }}>Impossibile caricare il menu (richiede il Postgres configurato in backend/.env).</p>
  }

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Cucina — menu della settimana</h1>

      {week.days.map((day) => (
        <Card key={day.day_of_week} label={DAY_LABELS[day.day_of_week]} icon={ChefHat} category="cucina">
          <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 220 }}>
              <p style={{ margin: '0 0 6px', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>Scuola</p>
              <div style={{ display: 'flex', gap: 8 }}>
                <input
                  value={drafts[day.day_of_week] ?? ''}
                  onChange={(e) => setDrafts((d) => ({ ...d, [day.day_of_week]: e.target.value }))}
                  placeholder="Es. Pasta al pomodoro"
                  style={inputStyle}
                />
                <button
                  style={buttonStyle}
                  onClick={() =>
                    upsertSchoolMenu.mutate({ day_of_week: day.day_of_week, meal_text: drafts[day.day_of_week] ?? '' })
                  }
                >
                  Salva
                </button>
              </div>
            </div>
            <div style={{ flex: 1, minWidth: 220 }}>
              <p style={{ margin: '0 0 6px', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
                Casa (sera)
              </p>
              <p style={{ margin: 0, fontSize: 'var(--fs-body)' }}>
                {day.day_of_week === new Date().getDay() ? day.home_meal ?? '—' : '—'}
              </p>
            </div>
          </div>
        </Card>
      ))}

      <p style={{ fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
        Il menu di casa mostra per ora solo il piatto del giorno corrente (l'app menu di casa esistente non espone
        ancora l'intera settimana — vedi TODO in backend/app/adapters/menu_app.py).
      </p>
    </>
  )
}
