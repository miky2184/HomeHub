import { useState } from 'react'
import { CheckCheck, Plus, ShoppingBasket, Trash2 } from 'lucide-react'
import { useAddShoppingItem, useRemoveShoppingItem, useShoppingList, useToggleShoppingItem } from '../api/hooks'
import { Card } from '../components/Card'
import { Modal } from '../components/Modal'
import { buttonStyle, ghostButtonStyle, inputStyle } from '../styles/controls'

export function ShoppingPage() {
  const { data: items, isLoading } = useShoppingList()
  const addItem = useAddShoppingItem()
  const toggleItem = useToggleShoppingItem()
  const removeItem = useRemoveShoppingItem()
  const [name, setName] = useState('')
  const [bulkPending, setBulkPending] = useState(false)
  const [confirmingDeleteAll, setConfirmingDeleteAll] = useState(false)

  function handleAdd() {
    if (!name.trim()) return
    addItem.mutate({ name: name.trim() }, { onSuccess: () => setName('') })
  }

  // In sequenza, non in parallelo: Bring! ha una sola lista condivisa e ogni
  // toggle/remove rilegge lo stato aggiornato alla fine — farle tutte insieme
  // rischierebbe che l'ultima risposta a tornare sovrascriva la cache con uno
  // stato che non riflette ancora le altre appena fatte.
  async function handleMarkAllBought() {
    const unchecked = (items ?? []).filter((item) => !item.checked)
    if (unchecked.length === 0) return
    setBulkPending(true)
    try {
      for (const item of unchecked) {
        await toggleItem.mutateAsync(item.id)
      }
    } finally {
      setBulkPending(false)
    }
  }

  async function handleDeleteAll() {
    setBulkPending(true)
    try {
      for (const item of items ?? []) {
        await removeItem.mutateAsync(item.id)
      }
    } finally {
      setBulkPending(false)
      setConfirmingDeleteAll(false)
    }
  }

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Lista della spesa</h1>

      <Card label="Aggiungi articolo" icon={Plus} category="spesa">
        <div style={{ display: 'flex', gap: 10 }}>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
            placeholder="Es. Latte"
            style={inputStyle}
          />
          <button style={buttonStyle} onClick={handleAdd}>Aggiungi</button>
        </div>
      </Card>

      {isLoading && <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>}

      <Card label={`Articoli · ${items?.length ?? 0}`} icon={ShoppingBasket} category="spesa">
        {(items?.length ?? 0) > 0 && (
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 14 }}>
            <button
              onClick={handleMarkAllBought}
              disabled={bulkPending || items!.every((i) => i.checked)}
              style={{ ...ghostButtonStyle, display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <CheckCheck size={16} /> Segna tutti comprati
            </button>
            <button
              onClick={() => setConfirmingDeleteAll(true)}
              disabled={bulkPending}
              style={{ ...ghostButtonStyle, display: 'flex', alignItems: 'center', gap: 6, color: 'var(--danger)' }}
            >
              <Trash2 size={16} /> Elimina tutti
            </button>
          </div>
        )}
        {(items ?? []).map((item) => (
          <div
            key={item.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '8px 0',
              borderBottom: '1px solid var(--border)',
            }}
          >
            <label style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer', flex: 1 }}>
              <input
                type="checkbox"
                checked={item.checked}
                onChange={() => toggleItem.mutate(item.id)}
                style={{ width: 20, height: 20 }}
              />
              <span
                style={{
                  fontSize: 'var(--fs-body)',
                  textDecoration: item.checked ? 'line-through' : 'none',
                  color: item.checked ? 'var(--text-muted)' : 'var(--text-primary)',
                }}
              >
                {item.name}
                {item.specification ? ` (${item.specification})` : ''}
              </span>
            </label>
            <button
              aria-label={`Rimuovi ${item.name}`}
              onClick={() => removeItem.mutate(item.id)}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
            >
              <Trash2 size={20} />
            </button>
          </div>
        ))}
      </Card>

      {confirmingDeleteAll && (
        <Modal title="Eliminare tutti gli articoli?" onClose={() => setConfirmingDeleteAll(false)}>
          <p style={{ margin: '0 0 16px', color: 'var(--text-secondary)' }}>
            Tutti i {items?.length ?? 0} articoli della lista verranno eliminati definitivamente.
          </p>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
            <button style={ghostButtonStyle} onClick={() => setConfirmingDeleteAll(false)}>
              Annulla
            </button>
            <button style={{ ...buttonStyle, background: 'var(--danger)' }} onClick={handleDeleteAll} disabled={bulkPending}>
              Elimina tutti
            </button>
          </div>
        </Modal>
      )}
    </>
  )
}
