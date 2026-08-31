import type { Shipment, ShipmentCarrier } from '../api/types'

/** "YYYY-MM-DDTHH:mm:ss..." (datetime ISO, non solo data come
 * lib/date.ts:formatShortDate) -> "DD/MM HH:mm", per gli eventi di
 * tracking che includono anche l'orario. */
export function formatEventDateTime(isoDateTime: string): string {
  const d = new Date(isoDateTime)
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  return `${day}/${month} ${hours}:${minutes}`
}

export const CARRIER_META: Record<ShipmentCarrier, { label: string; tracked: boolean }> = {
  poste_italiane: { label: 'Poste Italiane', tracked: true },
  altro: { label: 'Altro corriere', tracked: false },
}

export const CARRIER_OPTIONS: ShipmentCarrier[] = ['poste_italiane', 'altro']

/** Stato sintetico da mostrare in UI: consegnato, errore nell'ultimo
 * aggiornamento, ancora nessun dato, o l'ultimo stato grezzo del corriere. */
export function shipmentStatusInfo(shipment: Shipment): { label: string; color: string } {
  if (shipment.delivered) return { label: 'Consegnato', color: 'var(--accent)' }
  if (!CARRIER_META[shipment.carrier].tracked) return { label: 'Tracking manuale', color: 'var(--text-secondary)' }
  if (shipment.last_poll_error && !shipment.last_polled_at) {
    return { label: 'Nessun aggiornamento disponibile', color: 'var(--warning)' }
  }
  if (shipment.status) return { label: shipment.status, color: 'var(--text-primary)' }
  return { label: 'In transito', color: 'var(--text-secondary)' }
}

/** Riepilogo breve dell'ultimo evento, per la card compatta (tab e Home). */
export function lastEventSummary(shipment: Shipment): string | null {
  if (!shipment.last_event_description) return null
  const when = shipment.last_event_at ? formatEventDateTime(shipment.last_event_at) : null
  const where = shipment.last_event_location
  return [when, shipment.last_event_description, where].filter(Boolean).join(' · ')
}
