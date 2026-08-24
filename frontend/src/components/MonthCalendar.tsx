import { useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { getMonthGrid, isSameDay, toDateKey } from '../lib/date'

const WEEKDAY_LABELS = ['L', 'M', 'M', 'G', 'V', 'S', 'D']
const MONTH_LABELS = [
  'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
  'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre',
]

interface MonthCalendarProps {
  eventDateKeys: Set<string>
  selectedDate: Date
  onSelectDate: (date: Date) => void
}

export function MonthCalendar({ eventDateKeys, selectedDate, onSelectDate }: MonthCalendarProps) {
  const today = new Date()
  const [viewDate, setViewDate] = useState(() => new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1))

  const weeks = getMonthGrid(viewDate.getFullYear(), viewDate.getMonth())

  function changeMonth(delta: number) {
    setViewDate((d) => new Date(d.getFullYear(), d.getMonth() + delta, 1))
  }

  function goToday() {
    setViewDate(new Date(today.getFullYear(), today.getMonth(), 1))
    onSelectDate(today)
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <button onClick={() => changeMonth(-1)} aria-label="Mese precedente" style={navButtonStyle}>
          <ChevronLeft size={18} />
        </button>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
          <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 600 }}>
            {MONTH_LABELS[viewDate.getMonth()]} {viewDate.getFullYear()}
          </span>
          <button onClick={goToday} style={{ ...navButtonStyle, fontSize: 12, width: 'auto', padding: '4px 8px' }}>
            Oggi
          </button>
        </div>
        <button onClick={() => changeMonth(1)} aria-label="Mese successivo" style={navButtonStyle}>
          <ChevronRight size={18} />
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 4, marginBottom: 4 }}>
        {WEEKDAY_LABELS.map((label, i) => (
          <div key={i} style={{ textAlign: 'center', fontSize: 11, color: 'var(--text-muted)', fontWeight: 700 }}>
            {label}
          </div>
        ))}
      </div>

      {weeks.map((week, wi) => (
        <div key={wi} style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 4, marginBottom: 4 }}>
          {week.map((day) => {
            const inMonth = day.getMonth() === viewDate.getMonth()
            const isToday = isSameDay(day, today)
            const isSelected = isSameDay(day, selectedDate)
            const hasEvents = eventDateKeys.has(toDateKey(day))
            return (
              <button
                key={day.toISOString()}
                onClick={() => onSelectDate(day)}
                style={{
                  position: 'relative',
                  aspectRatio: '1',
                  border: isToday && !isSelected ? '2px solid var(--cat-agenda-fg)' : 'none',
                  borderRadius: '50%',
                  background: isSelected ? 'var(--cat-agenda-fg)' : 'transparent',
                  color: isSelected ? '#fff' : inMonth ? 'var(--text-primary)' : 'var(--text-muted)',
                  fontSize: 13,
                  fontWeight: isToday || isSelected ? 700 : 400,
                  cursor: 'pointer',
                }}
              >
                {day.getDate()}
                {hasEvents && (
                  <span
                    aria-hidden
                    style={{
                      position: 'absolute',
                      bottom: 3,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      width: 4,
                      height: 4,
                      borderRadius: '50%',
                      background: isSelected ? '#fff' : 'var(--cat-agenda-fg)',
                    }}
                  />
                )}
              </button>
            )
          })}
        </div>
      ))}
    </div>
  )
}

const navButtonStyle = {
  width: 28,
  height: 28,
  borderRadius: 'var(--radius-control)',
  border: 'none',
  background: 'transparent',
  color: 'var(--text-secondary)',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
} as const
