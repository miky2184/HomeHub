import { useNavigate } from 'react-router-dom'
import { useHomeSummary, useMarkTrainingDone, useToggleShoppingItem } from '../api/hooks'
import { Card } from '../components/Card'
import { StatusStrip } from '../components/StatusStrip'
import { DAY_LABELS, currentWeekStart } from '../lib/date'

export function HomePage() {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useHomeSummary()
  const toggleShoppingItem = useToggleShoppingItem()
  const markTrainingDone = useMarkTrainingDone(currentWeekStart())

  if (isLoading) return <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>
  if (isError || !data) {
    return <p style={{ color: 'var(--danger)' }}>Impossibile caricare i dati dal backend.</p>
  }

  return (
    <>
      <StatusStrip weather={data.weather} />

      <Card label="Oggi" onClick={() => navigate('/calendario')}>
        {data.today_events.length === 0 ? (
          <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-secondary)' }}>
            Nessun evento in programma
          </p>
        ) : (
          data.today_events.map((event) => (
            <div key={event.id} style={{ display: 'flex', gap: 12, alignItems: 'center', margin: '6px 0' }}>
              <span
                aria-hidden
                style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent)', flexShrink: 0 }}
              />
              <span style={{ fontSize: 'var(--fs-body)', color: 'var(--text-secondary)', width: 56, flexShrink: 0 }}>
                {new Intl.DateTimeFormat('it-IT', { hour: '2-digit', minute: '2-digit' }).format(new Date(event.start))}
              </span>
              <span style={{ fontSize: 'var(--fs-body)' }}>{event.title}</span>
            </div>
          ))
        )}
      </Card>

      <Card label="Menu di oggi" onClick={() => navigate('/menu')}>
        <div style={{ display: 'flex', gap: 20 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ margin: 0, fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>Scuola</p>
            <p style={{ margin: '4px 0 0', fontSize: 'var(--fs-body)' }}>
              {data.today_menu?.school_meal ?? '—'}
            </p>
          </div>
          <div style={{ flex: 1, minWidth: 0, borderLeft: '1px solid var(--border)', paddingLeft: 20 }}>
            <p style={{ margin: 0, fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>Casa (sera)</p>
            <p style={{ margin: '4px 0 0', fontSize: 'var(--fs-body)' }}>{data.today_menu?.home_meal ?? '—'}</p>
          </div>
        </div>
      </Card>

      <Card label="Prossimo allenamento" onClick={() => navigate('/allenamenti')}>
        {data.next_training ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ margin: 0, fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
                {DAY_LABELS[data.next_training.day_of_week]}
              </p>
              <p style={{ margin: '4px 0 0', fontSize: 'var(--fs-body)' }}>{data.next_training.session_text}</p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation()
                markTrainingDone.mutate({ id: data.next_training!.id, done: true })
              }}
              aria-label="Segna come fatto"
              style={{
                background: 'transparent',
                border: '2px solid var(--accent)',
                color: 'var(--accent)',
                borderRadius: '50%',
                width: 40,
                height: 40,
                cursor: 'pointer',
              }}
            >
              ✓
            </button>
          </div>
        ) : (
          <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-secondary)' }}>
            Nessun allenamento pianificato
          </p>
        )}
      </Card>

      <Card label={`Lista della spesa · ${data.shopping_total_count}`} onClick={() => navigate('/spesa')}>
        {data.shopping_preview.length === 0 ? (
          <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-secondary)' }}>Nessun articolo</p>
        ) : (
          data.shopping_preview.map((item) => (
            <label
              key={item.id}
              style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '6px 0', cursor: 'pointer' }}
              onClick={(e) => e.stopPropagation()}
            >
              <input
                type="checkbox"
                checked={item.checked}
                onChange={() => toggleShoppingItem.mutate(item.id)}
                style={{ width: 20, height: 20 }}
              />
              <span style={{ fontSize: 'var(--fs-body)' }}>{item.name}</span>
            </label>
          ))
        )}
      </Card>

      {data.inventory_alerts.length > 0 && (
        <Card label="Scorte in esaurimento" variant="warning" onClick={() => navigate('/inventory')}>
          <p style={{ margin: 0, fontSize: 'var(--fs-body)' }}>
            {data.inventory_alerts.map((a) => a.item_name).join(', ')}
          </p>
        </Card>
      )}
    </>
  )
}
