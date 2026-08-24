import { House } from 'lucide-react'
import { useInventoryAlerts } from '../api/hooks'
import { Card } from '../components/Card'
import type { InventoryAlert } from '../api/types'

const REASON_LABEL: Record<InventoryAlert['reason'], string> = {
  expired: 'Scaduto',
  critical: 'Scade a breve',
  warning: 'In scadenza',
}

const REASON_COLOR: Record<InventoryAlert['reason'], string> = {
  expired: 'var(--danger)',
  critical: 'var(--danger)',
  warning: 'var(--warning)',
}

export function InventoryPage() {
  const { data: alerts, isLoading } = useInventoryAlerts()

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Casa</h1>
      <p style={{ margin: '0 0 12px', color: 'var(--text-secondary)', fontSize: 'var(--fs-label)' }}>
        Sola lettura: per gestire gli oggetti (aggiungere, modificare, consumare) usa l'app Home Inventory.
      </p>

      {isLoading && <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>}

      {alerts?.length === 0 && <p style={{ color: 'var(--text-secondary)' }}>Nessun oggetto in scadenza ✓</p>}

      {(alerts ?? []).map((alert) => (
        <Card key={alert.id} label={REASON_LABEL[alert.reason]} icon={House} category="casa" variant="warning">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ margin: 0, fontSize: 'var(--fs-body)', fontWeight: 600, color: 'var(--text-primary)' }}>
                {alert.item_name}
                {alert.quantity != null ? ` — ${alert.quantity} ${alert.unit ?? ''}` : ''}
              </p>
              {alert.container_name && (
                <p style={{ margin: '2px 0 0', fontSize: 'var(--fs-label)', color: 'var(--text-secondary)' }}>
                  {alert.container_name}
                </p>
              )}
            </div>
            <span style={{ fontSize: 'var(--fs-body)', fontWeight: 700, color: REASON_COLOR[alert.reason] }}>
              {expiryLabel(alert.days_to_expiry)}
            </span>
          </div>
        </Card>
      ))}
    </>
  )
}

function expiryLabel(days: number | null): string {
  if (days == null) return ''
  if (days < 0) return `Scaduto da ${Math.abs(days)} gg`
  if (days === 0) return 'Scade oggi'
  return `Tra ${days} gg`
}
