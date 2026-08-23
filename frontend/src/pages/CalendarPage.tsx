import { useState } from 'react'
import { useAddCalendarEvent, useCalendarEvents } from '../api/hooks'
import { Card } from '../components/Card'
import { buttonStyle, inputStyle } from '../styles/controls'

export function CalendarPage() {
  const { data: events, isLoading } = useCalendarEvents()
  const addEvent = useAddCalendarEvent()
  const [title, setTitle] = useState('')
  const [start, setStart] = useState('')

  const sorted = [...(events ?? [])].sort((a, b) => a.start.localeCompare(b.start))

  function handleAdd() {
    if (!title.trim() || !start) return
    const startDate = new Date(start)
    const endDate = new Date(startDate.getTime() + 60 * 60_000)
    addEvent.mutate(
      {
        calendar_id: 'famiglia',
        title: title.trim(),
        start: startDate.toISOString(),
        end: endDate.toISOString(),
      },
      { onSuccess: () => setTitle('') },
    )
  }

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-heading)', margin: '4px 0 8px' }}>Calendario</h1>

      <Card label="Aggiungi evento">
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <input
            placeholder="Titolo evento"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            style={inputStyle}
          />
          <input
            type="datetime-local"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            style={inputStyle}
          />
          <button onClick={handleAdd} style={buttonStyle}>Aggiungi</button>
        </div>
      </Card>

      {isLoading && <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>}

      {sorted.map((event) => (
        <Card key={event.id} label={new Intl.DateTimeFormat('it-IT', { dateStyle: 'full' }).format(new Date(event.start))}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <span
              aria-hidden
              style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent)', flexShrink: 0 }}
            />
            <span style={{ fontSize: 'var(--fs-body)', color: 'var(--text-secondary)', width: 56 }}>
              {new Intl.DateTimeFormat('it-IT', { hour: '2-digit', minute: '2-digit' }).format(new Date(event.start))}
            </span>
            <span style={{ fontSize: 'var(--fs-body)' }}>{event.title}</span>
          </div>
        </Card>
      ))}
    </>
  )
}
