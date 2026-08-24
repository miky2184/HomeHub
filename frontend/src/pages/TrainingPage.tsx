import { useState } from 'react'
import { Dumbbell, Watch } from 'lucide-react'
import { useTrainingWeek } from '../api/hooks'
import { ActivityDetailModal } from '../components/ActivityDetailModal'
import { Card } from '../components/Card'
import { DAY_LABELS, currentWeekStart } from '../lib/date'

export function TrainingPage() {
  const weekStart = currentWeekStart()
  const { data: sessions, isLoading, isError } = useTrainingWeek(weekStart)
  const [openDetail, setOpenDetail] = useState<{ date: string; title: string } | null>(null)

  if (isLoading) return <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>
  if (isError || !sessions) {
    return (
      <p style={{ color: 'var(--danger)' }}>
        Impossibile caricare gli allenamenti (richiede il Postgres configurato in backend/.env).
      </p>
    )
  }

  function dateForDay(dayIndex: number): string {
    const d = new Date(weekStart)
    d.setDate(d.getDate() + dayIndex)
    return d.toISOString().slice(0, 10)
  }

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Attività — allenamenti della settimana</h1>
      <p style={{ fontSize: 'var(--fs-label)', color: 'var(--text-muted)', margin: '0 0 8px' }}>
        Piano letto da Garmin Connect; gli allenamenti svolti li programmi e sincronizzi da lì.
      </p>

      {DAY_LABELS.map((label, dayIndex) => {
        const session = sessions.find((s) => s.day_of_week === dayIndex)
        return (
          <Card key={dayIndex} label={label} icon={Dumbbell} category="attivita">
            {!session ? (
              <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-muted)' }}>—</p>
            ) : (
              <div
                onClick={() =>
                  session.done && setOpenDetail({ date: dateForDay(dayIndex), title: session.session_text })
                }
                style={{ cursor: session.done ? 'pointer' : 'default' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
                  <p style={{ margin: 0, fontSize: 'var(--fs-body)' }}>{session.session_text}</p>
                  <span
                    style={{
                      fontSize: 12,
                      fontWeight: 700,
                      padding: '4px 10px',
                      borderRadius: 12,
                      whiteSpace: 'nowrap',
                      background: session.done ? 'var(--cat-attivita-bg)' : 'var(--border)',
                      color: session.done ? 'var(--cat-attivita-fg)' : 'var(--text-muted)',
                    }}
                  >
                    {session.done ? 'Fatto' : 'Da fare'}
                  </span>
                </div>
                {session.garmin_note && (
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      marginTop: 10,
                      fontSize: 'var(--fs-label)',
                      color: 'var(--cat-attivita-fg)',
                    }}
                  >
                    <Watch size={15} />
                    <span>{session.garmin_note}</span>
                  </div>
                )}
              </div>
            )}
          </Card>
        )
      })}

      {openDetail && (
        <ActivityDetailModal date={openDetail.date} title={openDetail.title} onClose={() => setOpenDetail(null)} />
      )}
    </>
  )
}
