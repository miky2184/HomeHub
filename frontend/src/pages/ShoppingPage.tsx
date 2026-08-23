import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { useAddShoppingItem, useRemoveShoppingItem, useShoppingList, useToggleShoppingItem } from '../api/hooks'
import { Card } from '../components/Card'
import { buttonStyle, inputStyle } from '../styles/controls'

export function ShoppingPage() {
  const { data: items, isLoading } = useShoppingList()
  const addItem = useAddShoppingItem()
  const toggleItem = useToggleShoppingItem()
  const removeItem = useRemoveShoppingItem()
  const [name, setName] = useState('')

  function handleAdd() {
    if (!name.trim()) return
    addItem.mutate({ name: name.trim() }, { onSuccess: () => setName('') })
  }

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-heading)', margin: '4px 0 8px' }}>Lista della spesa</h1>

      <Card label="Aggiungi articolo">
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

      <Card label={`Articoli · ${items?.length ?? 0}`}>
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
    </>
  )
}
