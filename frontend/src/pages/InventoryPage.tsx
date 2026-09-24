import { useEffect, useState, type CSSProperties } from 'react'
import { Boxes, Check, House, Minus, Plus, Search, ShoppingCart } from 'lucide-react'
import { useAddShoppingItem, useAdjustItemQuantity, useInventoryAlerts, useInventoryContainers } from '../api/hooks'
import { Card } from '../components/Card'
import type { InventoryAlert, InventoryItem } from '../api/types'
import { formatShortDate } from '../lib/date'
import { ghostButtonStyle, inputStyle } from '../styles/controls'

const quantityBtnStyle: CSSProperties = {
  width: 28,
  height: 28,
  flexShrink: 0,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: 0,
  borderRadius: '50%',
  border: '1px solid var(--border-strong)',
  background: 'var(--bg-input)',
  color: 'var(--text-secondary)',
  cursor: 'pointer',
}

// quantity/unit contano "quante confezioni possediamo" (es. 3 pz);
// package_size è il formato di UNA di quelle confezioni (es. "400g") — due
// informazioni distinte, mostrate insieme solo qui in un'unica stringa
// leggibile (es. "3 pz da 400g").
function formatQuantity(quantity: number | null, unit: string | null, packageSize: string | null): string | null {
  if (quantity == null) return null
  const base = `${quantity} ${unit ?? ''}`.trim()
  return packageSize ? `${base} da ${packageSize}` : base
}

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
  const adjustQuantity = useAdjustItemQuantity()
  // Solo un feedback visivo locale ("Aggiunto ✓"): non c'è un modo per
  // sapere se un nome è già sulla lista Bring! senza interrogarla, e non
  // è comunque un problema — aggiungere due volte lo stesso nome aggiorna
  // la voce invece di duplicarla (vedi adapters/bring.py:save_item).
  const [added, setAdded] = useState<Set<number>>(new Set())
  const [selectedContainerId, setSelectedContainerId] = useState<number | null>(null)
  const [search, setSearch] = useState('')

  useEffect(() => {
    if (selectedContainerId === null && containers && containers.length > 0) {
      setSelectedContainerId(containers[0].id)
    }
  }, [containers, selectedContainerId])

  function handleAddToBring(alert: InventoryAlert) {
    const specification = formatQuantity(alert.quantity, alert.unit, alert.package_size) ?? undefined
    addShoppingItem.mutate(
      { name: alert.item_name, specification },
      { onSuccess: () => setAdded((prev) => new Set(prev).add(alert.id)) }
    )
  }

  function handleAdjust(itemId: number, delta: number) {
    adjustQuantity.mutate({ itemId, delta })
  }

  const selectedContainer = containers?.find((c) => c.id === selectedContainerId)

  // Ricerca trasversale: filtra gli oggetti già scaricati (containers include
  // già tutti gli items) su tutti i contenitori, non solo quello selezionato
  // — per trovare "dov'è finito il tonno" senza aprirli uno a uno. Un master
  // con figli (es. "Freezer") include già gli oggetti dei figli nella sua
  // stessa lista (vedi get_inventory_by_container) — dedup per item.id,
  // altrimenti un oggetto in "Cassetto 1" comparirebbe due volte (una volta
  // via "Freezer", una via "Cassetto 1" stesso); container_name (il figlio
  // preciso) batte il nome del master quando presente.
  const trimmedSearch = search.trim().toLowerCase()
  const searchResults = trimmedSearch
    ? Array.from(
        new Map(
          (containers ?? [])
            .flatMap((c) => c.items.map((item) => ({ item, containerName: item.container_name ?? c.name })))
            .filter(({ item }) => item.name.toLowerCase().includes(trimmedSearch))
            .map((entry) => [entry.item.id, entry] as const)
        ).values()
      )
    : null

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Casa</h1>
      <p style={{ margin: '0 0 12px', color: 'var(--text-secondary)', fontSize: 'var(--fs-label)' }}>
        Da qui puoi solo aggiustare le quantità (+/-); per aggiungere, modificare o eliminare oggetti
        usa l'app{' '}
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
                {formatQuantity(alert.quantity, alert.unit, alert.package_size)
                  ? ` — ${formatQuantity(alert.quantity, alert.unit, alert.package_size)}`
                  : ''}
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

      <Card label="Cerca in tutti i contenitori" icon={Search} category="casa">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Es. tonno, acqua, vino…"
          style={{ ...inputStyle, width: '100%' }}
        />

        {searchResults && searchResults.length === 0 && (
          <p style={{ margin: '12px 0 0', color: 'var(--text-muted)', fontSize: 'var(--fs-body)' }}>
            Nessun oggetto trovato.
          </p>
        )}

        {searchResults && searchResults.length > 0 && (
          <div style={{ marginTop: 12 }}>
            {searchResults.map(({ item, containerName }) => (
              <ItemRow
                key={item.id}
                item={item}
                subtitle={containerName}
                onAdjust={(delta) => handleAdjust(item.id, delta)}
                disabled={adjustQuantity.isPending}
              />
            ))}
          </div>
        )}
      </Card>

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
              <ItemRow
                key={item.id}
                item={item}
                // container_name presente = oggetto aggregato da un figlio
                // (contenitore master aperto, es. "Freezer"): mostra da quale
                // cassetto viene, oltre alla categoria.
                subtitle={[item.container_name, item.category].filter(Boolean).join(' · ') || null}
                onAdjust={(delta) => handleAdjust(item.id, delta)}
                disabled={adjustQuantity.isPending}
              />
            ))}
          </>
        )}
      </Card>
    </>
  )
}

function ItemRow({
  item,
  subtitle,
  onAdjust,
  disabled,
}: {
  item: InventoryItem
  subtitle?: string | null
  onAdjust: (delta: number) => void
  disabled: boolean
}) {
  return (
    <div
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
        {subtitle && (
          <span style={{ marginLeft: 8, fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>{subtitle}</span>
        )}
        {item.expiry_date && (
          <p style={{ margin: 0, fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
            Scad. {formatShortDate(item.expiry_date)}
          </p>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
        <button
          onClick={() => onAdjust(-1)}
          disabled={disabled}
          title="Diminuisci quantità"
          style={quantityBtnStyle}
        >
          <Minus size={14} />
        </button>
        <span style={{ minWidth: 44, textAlign: 'center' }}>
          <span style={{ display: 'block', fontSize: 'var(--fs-body)', color: 'var(--text-secondary)' }}>
            {item.quantity ?? '—'} {item.unit ?? ''}
          </span>
          {item.package_size && (
            <span style={{ display: 'block', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
              da {item.package_size}
            </span>
          )}
        </span>
        <button
          onClick={() => onAdjust(1)}
          disabled={disabled}
          title="Aumenta quantità"
          style={quantityBtnStyle}
        >
          <Plus size={14} />
        </button>
      </div>
    </div>
  )
}

function expiryLabel(days: number | null): string {
  if (days == null) return ''
  if (days < 0) return `Scaduto da ${Math.abs(days)} gg`
  if (days === 0) return 'Scade oggi'
  return `Tra ${days} gg`
}
