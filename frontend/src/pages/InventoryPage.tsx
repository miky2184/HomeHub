import { House } from 'lucide-react'
import { useInventoryAlerts, useMarkConsumed } from '../api/hooks'
import { Card } from '../components/Card'
import { buttonStyle } from '../styles/controls'

export function InventoryPage() {
  const { data: alerts, isLoading } = useInventoryAlerts()
  const markConsumed = useMarkConsumed()

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Casa</h1>

      {isLoading && <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>}

      {alerts?.length === 0 && (
        <p style={{ color: 'var(--text-secondary)' }}>Nessuna scorta in esaurimento al momento.</p>
      )}

      {(alerts ?? []).map((alert) => (
        <Card key={alert.id} label="Scorta in esaurimento" icon={House} category="casa" variant="warning">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <p style={{ margin: 0, fontSize: 'var(--fs-body)' }}>
              {alert.item_name}
              {alert.quantity != null ? ` — ${alert.quantity} ${alert.unit ?? ''}` : ''}
            </p>
            <button style={buttonStyle} onClick={() => markConsumed.mutate(alert.id)}>
              Segna gestito
            </button>
          </div>
        </Card>
      ))}
    </>
  )
}
