import { useEffect, useState } from 'react'
import { Boxes, Check, House, ShoppingCart } from 'lucide-react'
import { useAddShoppingItem, useInventoryAlerts, useInventoryContainers } from '../api/hooks'
import { Card } from '../components/Card'
import type { InventoryAlert } from '../api/types'
import { ghostButtonStyle, inputStyle } from '../styles/controls'

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
  const { data: containers, isLoading: isLoadingContainers } = useInventoryContainers()
  const addShoppingItem = useAddShoppingItem()
  // Solo un feedback visivo locale ("Aggiunto ✓"): non c'è un modo per
  // sapere se un nome è già sulla lista Bring! senza interrogarla, e non
  // è comunque un problema — aggiungere due volte lo stesso nome aggiorna
  // la voce invece di duplicarla (vedi adapters/bring.py:save_item).
  const [added, setAdded] = useState<Set<number>>(new Set())
  const [selectedContainerId, setSelectedContainerId] = useState<number | null>(null)

  useEffect(() => {
    if (selectedContainerId === null && containers && containers.length > 0) {
      setSelectedContainerId(containers[0].id)
    }
  }, [containers, selectedContainerId])

  function handleAddToBring(alert: InventoryAlert) {
    const specification =
      alert.quantity != null ? `${alert.quantity} ${alert.unit ?? ''}`.trim() : undefined
    addShoppingItem.mutate(
      { name: alert.item_name, specification },
      { onSuccess: () => setAdded((prev) => new Set(prev).add(alert.id)) }
    )
  }

  const selectedContainer = containers?.find((c) => c.id === selectedContainerId)

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Casa</h1>
      <p style={{ margin: '0 0 12px', color: 'var(--text-secondary)', fontSize: 'var(--fs-label)' }}>
        Sola lettura: per gestire gli oggetti (aggiungere, modificare, consumare) usa l'app{' '}
        <a
          href="https://miky2184.ddns.net:1032/"
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: 'var(--cat-casa-fg)', fontWeight: 700, textDecoration: 'none' }}
        >
          Home Inventory
        </a>
        .
      </p>

      {isLoading && <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>}

      {alerts?.length === 0 && <p style={{ color: 'var(--text-secondary)' }}>Nessun oggetto in scadenza ✓</p>}

      {(alerts ?? []).map((alert) => (
        <Card key={alert.id} label={REASON_LABEL[alert.reason]} icon={House} category="casa" variant="warning">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
            <div style={{ minWidth: 0 }}>
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
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexShrink: 0 }}>
              <span style={{ fontSize: 'var(--fs-body)', fontWeight: 700, color: REASON_COLOR[alert.reason] }}>
                {expiryLabel(alert.days_to_expiry)}
              </span>
              {added.has(alert.id) ? (
                <span
                  style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--accent)', fontSize: 'var(--fs-label)', fontWeight: 700 }}
                >
                  <Check size={16} /> Aggiunto
                </span>
              ) : (
                <button
                  onClick={() => handleAddToBring(alert)}
                  disabled={addShoppingItem.isPending}
                  style={{ ...ghostButtonStyle, display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <ShoppingCart size={16} /> Aggiungi a Bring!
                </button>
              )}
            </div>
          </div>
        </Card>
      ))}

      <Card label="Sfoglia per contenitore" icon={Boxes} category="casa">
        {isLoadingContainers && <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>}

        {!isLoadingContainers && (containers ?? []).length === 0 && (
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: 'var(--fs-body)' }}>
            Nessun contenitore trovato in Home Inventory.
          </p>
        )}

        {containers && containers.length > 0 && (
          <>
            <select
              value={selectedContainerId ?? ''}
              onChange={(e) => setSelectedContainerId(Number(e.target.value))}
              style={{ ...inputStyle, width: '100%', marginBottom: 12 }}
            >
              {containers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.items.length})
                </option>
              ))}
            </select>

            {selectedContainer && selectedContainer.items.length === 0 && (
              <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: 'var(--fs-body)' }}>Vuoto</p>
            )}

            {selectedContainer?.items.map((item) => (
              <div
                key={item.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: 12,
                  padding: '6px 0',
                  borderBottom: '1px solid var(--border)',
                }}
              >
                <div style={{ minWidth: 0 }}>
                  <span style={{ fontSize: 'var(--fs-body)', color: 'var(--text-primary)', fontWeight: 600 }}>
                    {item.name}
                  </span>
                  {item.category && (
                    <span style={{ marginLeft: 8, fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
                      {item.category}
                    </span>
                  )}
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  {item.quantity != null && (
                    <span style={{ fontSize: 'var(--fs-body)', color: 'var(--text-secondary)' }}>
                      {item.quantity} {item.unit ?? ''}
                    </span>
                  )}
                  {item.expiry_date && (
                    <p style={{ margin: 0, fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
                      Scad. {formatShortDate(item.expiry_date)}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </>
        )}
      </Card>
    </>
  )
}

function expiryLabel(days: number | null): string {
  if (days == null) return ''
  if (days < 0) return `Scaduto da ${Math.abs(days)} gg`
  if (days === 0) return 'Scade oggi'
  return `Tra ${days} gg`
}

function formatShortDate(dateKey: string): string {
  const [, m, d] = dateKey.split('-')
  return `${d}/${m}`
}
