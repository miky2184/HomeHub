import { useState } from 'react'
import { Package, Pencil, Plus, RefreshCw, Trash2 } from 'lucide-react'
import { useCreateShipment, useDeleteShipment, useRefreshShipment, useShipments, useUpdateShipment } from '../api/hooks'
import type { Shipment, ShipmentInput } from '../api/types'
import { Card } from '../components/Card'
import { Modal } from '../components/Modal'
import { useUnsavedChanges } from '../hooks/useUnsavedChanges'
import { CARRIER_META, CARRIER_OPTIONS, formatEventDateTime, lastEventSummary, shipmentStatusInfo } from '../lib/shipments'
import { buttonStyle, ghostButtonStyle, inputStyle } from '../styles/controls'

const EMPTY_FORM: ShipmentInput = { tracking_number: '', carrier: 'poste_italiane', label: null }

export function ShipmentsPage() {
  const { data: shipments, isLoading } = useShipments()
  const createShipment = useCreateShipment()
  const updateShipment = useUpdateShipment()
  const deleteShipment = useDeleteShipment()
  const refreshShipment = useRefreshShipment()

  const [form, setForm] = useState<ShipmentInput>(EMPTY_FORM)
  const [editing, setEditing] = useState<Shipment | null>(null)
  const [deleting, setDeleting] = useState<Shipment | null>(null)
  const [viewing, setViewing] = useState<Shipment | null>(null)

  // Vedi TodoPage/ChoresPage: non perdere una spedizione a metà inserimento
  // o una modale di modifica aperta solo perché è scattato l'idle redirect.
  useUnsavedChanges(form.tracking_number.trim() !== '' || editing !== null)

  function handleCreate() {
    if (!form.tracking_number.trim()) return
    createShipment.mutate(
      { ...form, tracking_number: form.tracking_number.trim(), label: form.label?.trim() || null },
      { onSuccess: () => setForm(EMPTY_FORM) }
    )
  }

  const inTransit = (shipments ?? []).filter((s) => !s.delivered)
  const delivered = (shipments ?? []).filter((s) => s.delivered)

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Spedizioni</h1>
      <p style={{ margin: '0 0 12px', color: 'var(--text-secondary)', fontSize: 'var(--fs-label)' }}>
        Solo Poste Italiane si aggiorna in automatico; per altri corrieri puoi comunque tenere traccia del
        numero, senza stato in tempo reale.
      </p>

      <Card label="Nuova spedizione" icon={Plus} category="spedizioni">
        <ShipmentFormFields value={form} onChange={setForm} />
        <button style={{ ...buttonStyle, marginTop: 10 }} onClick={handleCreate}>
          Aggiungi
        </button>
      </Card>

      {isLoading && <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>}

      <Card label={`In transito · ${inTransit.length}`} icon={Package} category="spedizioni">
        {inTransit.length === 0 && (
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: 'var(--fs-body)' }}>
            Nessuna spedizione in transito.
          </p>
        )}
        {inTransit.map((shipment) => (
          <ShipmentRow
            key={shipment.id}
            shipment={shipment}
            onView={() => setViewing(shipment)}
            onEdit={() => setEditing(shipment)}
            onDelete={() => setDeleting(shipment)}
            onRefresh={() => refreshShipment.mutate(shipment.id)}
            refreshing={refreshShipment.isPending && refreshShipment.variables === shipment.id}
          />
        ))}
      </Card>

      {delivered.length > 0 && (
        <Card label={`Consegnate · ${delivered.length}`} icon={Package} category="spedizioni">
          {delivered.map((shipment) => (
            <ShipmentRow
              key={shipment.id}
              shipment={shipment}
              onView={() => setViewing(shipment)}
              onEdit={() => setEditing(shipment)}
              onDelete={() => setDeleting(shipment)}
              onRefresh={() => refreshShipment.mutate(shipment.id)}
              refreshing={refreshShipment.isPending && refreshShipment.variables === shipment.id}
            />
          ))}
        </Card>
      )}

      {editing && (
        <Modal title="Modifica spedizione" onClose={() => setEditing(null)}>
          <ShipmentFormFields
            value={{ tracking_number: editing.tracking_number, carrier: editing.carrier, label: editing.label }}
            onChange={(next) => setEditing({ ...editing, ...next })}
          />
          <button
            style={{ ...buttonStyle, marginTop: 14, width: '100%' }}
            onClick={() =>
              updateShipment.mutate(
                {
                  id: editing.id,
                  tracking_number: editing.tracking_number.trim(),
                  carrier: editing.carrier,
                  label: editing.label?.trim() || null,
                },
                { onSuccess: () => setEditing(null) }
              )
            }
          >
            Salva
          </button>
        </Modal>
      )}

      {deleting && (
        <Modal title="Eliminare questa spedizione?" onClose={() => setDeleting(null)}>
          <p style={{ margin: '0 0 16px', color: 'var(--text-secondary)' }}>
            «{deleting.label || deleting.tracking_number}» verrà eliminata definitivamente.
          </p>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
            <button style={ghostButtonStyle} onClick={() => setDeleting(null)}>
              Annulla
            </button>
            <button
              style={{ ...buttonStyle, background: 'var(--danger)' }}
              onClick={() => deleteShipment.mutate(deleting.id, { onSuccess: () => setDeleting(null) })}
            >
              Elimina
            </button>
          </div>
        </Modal>
      )}

      {viewing && (
        <Modal title={viewing.label || viewing.tracking_number} onClose={() => setViewing(null)}>
          <p style={{ margin: '0 0 4px', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
            {CARRIER_META[viewing.carrier].label} · {viewing.tracking_number}
          </p>
          {viewing.last_poll_error && (
            <p style={{ margin: '8px 0', fontSize: 'var(--fs-label)', color: 'var(--warning)' }}>
              Ultimo aggiornamento non riuscito: {viewing.last_poll_error}
            </p>
          )}
          {viewing.events.length === 0 && (
            <p style={{ margin: '12px 0 0', color: 'var(--text-secondary)', fontSize: 'var(--fs-body)' }}>
              Nessuno storico disponibile ancora.
            </p>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 12 }}>
            {[...viewing.events].reverse().map((event, i) => (
              <div key={i} style={{ borderLeft: '2px solid var(--cat-spedizioni-fg)', paddingLeft: 10 }}>
                <p style={{ margin: 0, fontSize: 'var(--fs-label)', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {formatEventDateTime(event.at)}
                </p>
                <p style={{ margin: 0, fontSize: 'var(--fs-label)', color: 'var(--text-secondary)' }}>
                  {event.description}
                  {event.location ? ` · ${event.location}` : ''}
                </p>
              </div>
            ))}
          </div>
        </Modal>
      )}
    </>
  )
}

function ShipmentRow({
  shipment,
  onView,
  onEdit,
  onDelete,
  onRefresh,
  refreshing,
}: {
  shipment: Shipment
  onView: () => void
  onEdit: () => void
  onDelete: () => void
  onRefresh: () => void
  refreshing: boolean
}) {
  const status = shipmentStatusInfo(shipment)
  const eventSummary = lastEventSummary(shipment)
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
      <div style={{ flex: 1, minWidth: 0, cursor: 'pointer' }} onClick={onView}>
        <p style={{ margin: 0, fontSize: 'var(--fs-body)', fontWeight: 600, color: 'var(--text-primary)' }}>
          {shipment.label || shipment.tracking_number}
        </p>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 4 }}>
          <span style={{ fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
            {CARRIER_META[shipment.carrier].label}
          </span>
          <span style={{ fontSize: 'var(--fs-label)', fontWeight: 700, color: status.color }}>{status.label}</span>
        </div>
        {eventSummary && (
          <p style={{ margin: '4px 0 0', fontSize: 'var(--fs-label)', color: 'var(--text-secondary)' }}>{eventSummary}</p>
        )}
      </div>
      {CARRIER_META[shipment.carrier].tracked && (
        <button
          aria-label={`Aggiorna ${shipment.label || shipment.tracking_number}`}
          onClick={onRefresh}
          disabled={refreshing}
          style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
        >
          <RefreshCw size={18} className={refreshing ? 'spin' : undefined} />
        </button>
      )}
      <button
        aria-label={`Modifica ${shipment.label || shipment.tracking_number}`}
        onClick={onEdit}
        style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
      >
        <Pencil size={18} />
      </button>
      <button
        aria-label={`Elimina ${shipment.label || shipment.tracking_number}`}
        onClick={onDelete}
        style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
      >
        <Trash2 size={18} />
      </button>
    </div>
  )
}

function ShipmentFormFields({ value, onChange }: { value: ShipmentInput; onChange: (value: ShipmentInput) => void }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <input
        value={value.tracking_number}
        onChange={(e) => onChange({ ...value, tracking_number: e.target.value })}
        placeholder="Numero di tracking"
        style={inputStyle}
      />
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <select
          value={value.carrier}
          onChange={(e) => onChange({ ...value, carrier: e.target.value as ShipmentInput['carrier'] })}
          style={inputStyle}
        >
          {CARRIER_OPTIONS.map((c) => (
            <option key={c} value={c}>
              {CARRIER_META[c].label}
            </option>
          ))}
        </select>
        <input
          value={value.label ?? ''}
          onChange={(e) => onChange({ ...value, label: e.target.value })}
          placeholder="Nota (facoltativa, es. Scarpe Sofia)"
          style={inputStyle}
        />
      </div>
    </div>
  )
}
