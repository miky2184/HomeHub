import { Umbrella } from 'lucide-react'
import type { WeatherSnapshot } from '../api/types'
import { iconForCondition } from '../lib/weatherIcon'
import { Card } from './Card'

const DAY_AHEAD_LABELS = ['Domani', 'Dopodomani']

function formatHour(iso: string): string {
  return `${new Date(iso).getHours()}:00`
}

export function WeatherCard({ weather }: { weather: WeatherSnapshot }) {
  const CurrentIcon = iconForCondition(weather.condition)

  return (
    <Card label={weather.city ? `Meteo · ${weather.city}` : 'Meteo'} icon={CurrentIcon} category="agenda">
      <div style={{ display: 'flex', alignItems: 'stretch', gap: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <CurrentIcon size={40} />
          <div>
            <p style={{ margin: 0, fontSize: 34, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
              {weather.temperature_c != null ? `${Math.round(weather.temperature_c)}°` : '—'}
            </p>
            {weather.condition && (
              <p style={{ margin: '4px 0 0', fontSize: 'var(--fs-label)', color: 'var(--text-secondary)' }}>
                {weather.condition}
              </p>
            )}
          </div>
        </div>

        {weather.hourly.length > 0 && (
          <>
            <div style={{ width: 1, background: 'var(--border)', alignSelf: 'stretch' }} />
            <div style={{ display: 'flex', flex: 1, justifyContent: 'space-between', gap: 8 }}>
              {weather.hourly.map((h) => {
                const HourIcon = iconForCondition(h.condition)
                return (
                  <div key={h.time} style={{ textAlign: 'center' }}>
                    <p style={{ margin: '0 0 6px', fontSize: 11, color: 'var(--text-muted)' }}>{formatHour(h.time)}</p>
                    <HourIcon size={20} />
                    <p style={{ margin: '6px 0 0', fontSize: 'var(--fs-label)', fontWeight: 600 }}>
                      {h.temperature_c != null ? `${Math.round(h.temperature_c)}°` : '—'}
                    </p>
                  </div>
                )
              })}
            </div>
          </>
        )}
      </div>

      {weather.precipitation_alert && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginTop: 14,
            padding: '8px 12px',
            borderRadius: 'var(--radius-control)',
            background: '#fbe9df',
          }}
        >
          <Umbrella size={18} color="var(--warning)" />
          <span style={{ fontSize: 'var(--fs-label)', fontWeight: 700, color: 'var(--warning)' }}>
            {weather.precipitation_alert}
          </span>
        </div>
      )}

      {weather.daily.length > 0 && (
        <div style={{ display: 'flex', gap: 20, marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border)' }}>
          {weather.daily.map((d, i) => {
            const DayIcon = iconForCondition(d.condition)
            return (
              <div key={d.date} style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 0 }}>
                <DayIcon size={24} />
                <div style={{ minWidth: 0 }}>
                  <p style={{ margin: 0, fontSize: 'var(--fs-label)', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {DAY_AHEAD_LABELS[i] ?? ''}
                  </p>
                  <p style={{ margin: '2px 0 0', fontSize: 'var(--fs-label)', color: 'var(--text-secondary)' }}>
                    {d.temperature_min != null && d.temperature_max != null
                      ? `${Math.round(d.temperature_min)}° / ${Math.round(d.temperature_max)}°`
                      : '—'}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </Card>
  )
}
