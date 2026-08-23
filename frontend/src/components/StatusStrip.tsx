import { Sun } from 'lucide-react'
import { useClock } from '../hooks/useClock'
import type { WeatherSnapshot } from '../api/types'

interface StatusStripProps {
  weather?: WeatherSnapshot | null
}

export function StatusStrip({ weather }: StatusStripProps) {
  const { time, date } = useClock()

  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
      <div>
        <p style={{ margin: 0, fontSize: 'var(--fs-clock)', fontWeight: 600, lineHeight: 1 }}>{time}</p>
        <p style={{ margin: '6px 0 0', fontSize: 'var(--fs-date)', color: 'var(--text-secondary)' }}>{date}</p>
      </div>
      {weather?.temperature_c != null && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--accent)' }}>
          <Sun size={28} />
          <span style={{ fontSize: 'var(--fs-heading)', fontWeight: 600 }}>{Math.round(weather.temperature_c)}°</span>
        </div>
      )}
    </div>
  )
}
