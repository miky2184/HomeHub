import { Cloud, CloudDrizzle, CloudFog, CloudLightning, CloudRain, CloudSnow, Sun } from 'lucide-react'
import type { ComponentType } from 'react'

/** Icona in base alla descrizione testuale già tradotta dal backend (vedi
 * WMO_CONDITIONS in backend/app/adapters/weather.py) — euristica su parole
 * chiave, stesso approccio già usato per eventi/allenamenti in questa app. */
export function iconForCondition(condition: string | null): ComponentType<{ size?: number }> {
  if (!condition) return Sun
  const key = condition.toLowerCase()
  if (key.includes('temporale')) return CloudLightning
  if (key.includes('neve')) return CloudSnow
  if (key.includes('pioviggine')) return CloudDrizzle
  if (key.includes('pioggia') || key.includes('rovesci')) return CloudRain
  if (key.includes('nebbia')) return CloudFog
  if (key.includes('nuvoloso')) return Cloud
  return Sun
}
