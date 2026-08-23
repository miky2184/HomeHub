import { useEffect, useState } from 'react'
import { Dumbbell } from 'lucide-react'
import { useMarkTrainingDone, useTrainingWeek, useUpsertTrainingSession } from '../api/hooks'
import { Card } from '../components/Card'
import { DAY_LABELS, currentWeekStart } from '../lib/date'
import { buttonStyle, inputStyle } from '../styles/controls'

export function TrainingPage() {
  const weekStart = currentWeekStart()
  const { data: sessions, isLoading, isError } = useTrainingWeek(weekStart)
  const upsertSession = useUpsertTrainingSession(weekStart)
  const markDone = useMarkTrainingDone(weekStart)
  const [drafts, setDrafts] = useState<Record<number, string>>({})

  useEffect(() => {
    if (!sessions) return
    const next: Record<number, string> = {}
    sessions.forEach((s) => {
      next[s.day_of_week] = s.session_text
    })
    setDrafts(next)
  }, [sessions])

  if (isLoading) return <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>
  if (isError || !sessions) {
    return <p style={{ color: 'var(--danger)' }}>Impossibile caricare gli allenamenti (richiede il Postgres configurato in backend/.env).</p>
  }

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Attività — allenamenti della settimana</h1>
      <p style={{ fontSize: 'var(--fs-label)', color: 'var(--text-muted)', margin: '0 0 8px' }}>
        Piano comunicato dal coach via WhatsApp: inseriscilo qui giorno per giorno.
      </p>

      {DAY_LABELS.map((label, dayIndex) => {
        const existing = sessions.find((s) => s.day_of_week === dayIndex)
        return (
          <Card key={dayIndex} label={label} icon={Dumbbell} category="attivita">
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              <input
                value={drafts[dayIndex] ?? ''}
                onChange={(e) => setDrafts((d) => ({ ...d, [dayIndex]: e.target.value }))}
                placeholder="Es. Corsa 8km + core"
                style={inputStyle}
              />
              <button
                style={buttonStyle}
                onClick={() => upsertSession.mutate({ day_of_week: dayIndex, session_text: drafts[dayIndex] ?? '' })}
              >
                Salva
              </button>
              {existing && (
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 'var(--fs-label)' }}>
                  <input
                    type="checkbox"
                    checked={existing.done}
                    onChange={(e) => markDone.mutate({ id: existing.id, done: e.target.checked })}
                    style={{ width: 20, height: 20 }}
                  />
                  Fatto
                </label>
              )}
            </div>
          </Card>
        )
      })}
    </>
  )
}
