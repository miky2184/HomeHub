import { useEffect, useMemo, useState } from 'react'
import { CalendarDays, Plus } from 'lucide-react'
import type { CalendarEvent } from '../api/types'
import { useAddCalendarEvent, useCalendarEvents, useCalendars } from '../api/hooks'
import { Card } from '../components/Card'
import { MonthCalendar } from '../components/MonthCalendar'
import { DAY_LABELS, getWeekDates, isSameDay, toDateKey } from '../lib/date'
import { buttonStyle, inputStyle } from '../styles/controls'

function EventRow({ event }: { event: CalendarEvent }) {
  return (
    <div style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '6px 0' }}>
      <span
        aria-hidden
        style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--cat-agenda-fg)', flexShrink: 0 }}
      />
      <span style={{ fontSize: 'var(--fs-label)', color: 'var(--text-secondary)', width: 90, flexShrink: 0 }}>
        {event.all_day
          ? 'Tutto il giorno'
          : new Intl.DateTimeFormat('it-IT', { hour: '2-digit', minute: '2-digit' }).format(new Date(event.start))}
      </span>
      <span style={{ fontSize: 'var(--fs-body)' }}>{event.title}</span>
    </div>
  )
}

export function CalendarPage() {
  const { data: events, isLoading } = useCalendarEvents()
  const { data: calendars } = useCalendars()
  const addEvent = useAddCalendarEvent()
  const [title, setTitle] = useState('')
  const [start, setStart] = useState('')
  const [calendarId, setCalendarId] = useState('')
  const [selectedDate, setSelectedDate] = useState(() => new Date())

  useEffect(() => {
    if (!calendarId && calendars && calendars.length > 0) setCalendarId(calendars[0].id)
  }, [calendars, calendarId])

  const sorted = useMemo(() => [...(events ?? [])].sort((a, b) => a.start.localeCompare(b.start)), [events])

  const eventsByDay = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>()
    for (const event of sorted) {
      const key = toDateKey(new Date(event.start))
      if (!map.has(key)) map.set(key, [])
      map.get(key)!.push(event)
    }
    return map
  }, [sorted])

  const eventDateKeys = useMemo(() => new Set(eventsByDay.keys()), [eventsByDay])
  const selectedDayEvents = eventsByDay.get(toDateKey(selectedDate)) ?? []
  const weekDates = useMemo(() => getWeekDates(new Date()), [])

  function handleAdd() {
    if (!title.trim() || !start || !calendarId) return
    const startDate = new Date(start)
    const endDate = new Date(startDate.getTime() + 60 * 60_000)
    addEvent.mutate(
      {
        calendar_id: calendarId,
        title: title.trim(),
        start: startDate.toISOString(),
        end: endDate.toISOString(),
      },
      { onSuccess: () => setTitle('') },
    )
  }

  if (isLoading) return <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Agenda</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--gap-md)' }}>
        <Card label="Calendario" icon={CalendarDays} category="agenda">
          <MonthCalendar eventDateKeys={eventDateKeys} selectedDate={selectedDate} onSelectDate={setSelectedDate} />
        </Card>

        <Card
          label={new Intl.DateTimeFormat('it-IT', { dateStyle: 'full' }).format(selectedDate)}
          icon={CalendarDays}
          category="agenda"
        >
          {selectedDayEvents.length === 0 ? (
            <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-secondary)' }}>Nessun evento</p>
          ) : (
            selectedDayEvents.map((event) => <EventRow key={event.id} event={event} />)
          )}
        </Card>
      </div>

      <Card label="Questa settimana" icon={CalendarDays} category="agenda">
        {weekDates.map((day, i) => {
          const dayEvents = eventsByDay.get(toDateKey(day)) ?? []
          const isToday = isSameDay(day, new Date())
          return (
            <div key={i} style={{ padding: '8px 0', borderBottom: i < 6 ? '1px solid var(--border)' : 'none' }}>
              <p
                style={{
                  margin: '0 0 4px',
                  fontSize: 'var(--fs-label)',
                  fontWeight: 700,
                  color: isToday ? 'var(--cat-agenda-fg)' : 'var(--text-muted)',
                }}
              >
                {DAY_LABELS[(day.getDay() + 6) % 7]} {day.getDate()}
              </p>
              {dayEvents.length === 0 ? (
                <p style={{ margin: 0, fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>—</p>
              ) : (
                dayEvents.map((event) => <EventRow key={event.id} event={event} />)
              )}
            </div>
          )
        })}
      </Card>

      <Card label="Aggiungi evento" icon={Plus} category="agenda">
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <input
            placeholder="Titolo evento"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            style={inputStyle}
          />
          <input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} style={inputStyle} />
          {calendars && calendars.length > 1 && (
            <select value={calendarId} onChange={(e) => setCalendarId(e.target.value)} style={inputStyle}>
              {calendars.map((cal) => (
                <option key={cal.id} value={cal.id}>
                  {cal.label}
                </option>
              ))}
            </select>
          )}
          <button onClick={handleAdd} style={buttonStyle}>
            Aggiungi
          </button>
        </div>
      </Card>
    </>
  )
}
