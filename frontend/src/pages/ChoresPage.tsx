import { useState } from 'react'
import { Check, Pencil, Plus, Trash2, Wrench } from 'lucide-react'
import { useCreateChore, useDeleteChore, useChores, useUpdateChore } from '../api/hooks'
import type { Chore, ChoreInput } from '../api/types'
import { Card } from '../components/Card'
import { Modal } from '../components/Modal'
import { choreDueInfo, intervalLabel } from '../lib/chores'
import { toDateKey } from '../lib/date'
import { buttonStyle, ghostButtonStyle, inputStyle } from '../styles/controls'

const INTERVAL_PRESETS = [
  { label: '1 sett.', days: 7 },
  { label: '2 sett.', days: 14 },
  { label: '1 mese', days: 30 },
  { label: '3 mesi', days: 90 },
  { label: '6 mesi', days: 180 },
  { label: '1 anno', days: 365 },
]

const EMPTY_FORM: ChoreInput = { title: '', interval_days: 30, last_done_date: null, assignee: null, notes: null }

export function ChoresPage() {
  const { data: chores, isLoading } = useChores()
  const createChore = useCreateChore()
  const updateChore = useUpdateChore()
  const deleteChore = useDeleteChore()

  const [form, setForm] = useState<ChoreInput>(EMPTY_FORM)
  const [editing, setEditing] = useState<Chore | null>(null)
  const [deleting, setDeleting] = useState<Chore | null>(null)

  function handleCreate() {
    if (!form.title.trim() || !form.interval_days || form.interval_days < 1) return
    createChore.mutate(
      { ...form, title: form.title.trim(), assignee: form.assignee?.trim() || null, notes: form.notes?.trim() || null },
      { onSuccess: () => setForm(EMPTY_FORM) }
    )
  }

  function markDoneToday(chore: Chore) {
    updateChore.mutate({ id: chore.id, last_done_date: toDateKey(new Date()) })
  }

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Manutenzione</h1>
      <p style={{ margin: '0 0 12px', color: 'var(--text-secondary)', fontSize: 'var(--fs-label)' }}>
        Attività di casa che si ripetono a intervalli (filtri, piante, manutenzioni…), non cose puntuali —
        per quelle usa il Todo.
      </p>

      <Card label="Nuova attività" icon={Plus} category="manutenzione">
        <ChoreFormFields value={form} onChange={setForm} />
        <button style={{ ...buttonStyle, marginTop: 10 }} onClick={handleCreate}>
          Aggiungi
        </button>
      </Card>

      {isLoading && <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>}

      <Card label={`Attività · ${(chores ?? []).length}`} icon={Wrench} category="manutenzione">
        {chores?.length === 0 && (
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: 'var(--fs-body)' }}>
            Nessuna attività ricorrente ancora. Aggiungine una sopra.
          </p>
        )}
        {chores?.map((chore) => {
          const due = choreDueInfo(chore)
          return (
            <div
              key={chore.id}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 12,
                padding: '10px 0',
                borderBottom: '1px solid var(--border)',
              }}
            >
              <button
                onClick={() => markDoneToday(chore)}
                aria-label={`Segna "${chore.title}" come fatta oggi`}
                title="Fatto oggi"
                style={{
                  width: 30,
                  height: 30,
                  borderRadius: '50%',
                  border: '1px solid var(--border-strong)',
                  background: 'var(--cat-manutenzione-bg)',
                  color: 'var(--cat-manutenzione-fg)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  flexShrink: 0,
                  marginTop: 2,
                }}
              >
                <Check size={16} />
              </button>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ margin: 0, fontSize: 'var(--fs-body)', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {chore.title}
                </p>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 4 }}>
                  <span style={{ fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
                    {intervalLabel(chore.interval_days)}
                  </span>
                  {chore.assignee && (
                    <span style={{ fontSize: 'var(--fs-label)', color: 'var(--text-secondary)' }}>{chore.assignee}</span>
                  )}
                  <span
                    style={{
                      fontSize: 'var(--fs-label)',
                      fontWeight: due.overdue ? 700 : 400,
                      color: due.overdue ? 'var(--danger)' : 'var(--text-secondary)',
                    }}
                  >
                    {due.label}
                  </span>
                </div>
                {chore.notes && (
                  <p style={{ margin: '4px 0 0', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>{chore.notes}</p>
                )}
              </div>
              <button
                aria-label={`Modifica ${chore.title}`}
                onClick={() => setEditing(chore)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <Pencil size={18} />
              </button>
              <button
                aria-label={`Elimina ${chore.title}`}
                onClick={() => setDeleting(chore)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <Trash2 size={18} />
              </button>
            </div>
          )
        })}
      </Card>

      {editing && (
        <Modal title="Modifica attività" onClose={() => setEditing(null)}>
          <ChoreFormFields
            value={{
              title: editing.title,
              interval_days: editing.interval_days,
              last_done_date: editing.last_done_date,
              assignee: editing.assignee,
              notes: editing.notes,
            }}
            onChange={(next) => setEditing({ ...editing, ...next })}
          />
          <button
            style={{ ...buttonStyle, marginTop: 14, width: '100%' }}
            onClick={() =>
              updateChore.mutate(
                {
                  id: editing.id,
                  title: editing.title.trim(),
                  interval_days: editing.interval_days,
                  last_done_date: editing.last_done_date,
                  assignee: editing.assignee?.trim() || null,
                  notes: editing.notes?.trim() || null,
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
        <Modal title="Eliminare questa attività?" onClose={() => setDeleting(null)}>
          <p style={{ margin: '0 0 16px', color: 'var(--text-secondary)' }}>
            «{deleting.title}» verrà eliminata definitivamente.
          </p>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
            <button style={ghostButtonStyle} onClick={() => setDeleting(null)}>
              Annulla
            </button>
            <button
              style={{ ...buttonStyle, background: 'var(--danger)' }}
              onClick={() => deleteChore.mutate(deleting.id, { onSuccess: () => setDeleting(null) })}
            >
              Elimina
            </button>
          </div>
        </Modal>
      )}
    </>
  )
}

function ChoreFormFields({ value, onChange }: { value: ChoreInput; onChange: (value: ChoreInput) => void }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <input
        value={value.title}
        onChange={(e) => onChange({ ...value, title: e.target.value })}
        placeholder="Es. Pulire filtro lavastoviglie"
        style={inputStyle}
      />
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {INTERVAL_PRESETS.map((preset) => (
          <button
            key={preset.days}
            type="button"
            onClick={() => onChange({ ...value, interval_days: preset.days })}
            style={{
              ...ghostButtonStyle,
              padding: '6px 12px',
              fontSize: 12,
              background: value.interval_days === preset.days ? 'var(--cat-manutenzione-bg)' : 'var(--bg-input)',
              color: value.interval_days === preset.days ? 'var(--cat-manutenzione-fg)' : 'var(--text-secondary)',
              borderColor: value.interval_days === preset.days ? 'var(--cat-manutenzione-fg)' : 'var(--border-strong)',
            }}
          >
            {preset.label}
          </button>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <div>
          <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
            Ogni quanti giorni
          </label>
          <input
            type="number"
            min={1}
            value={value.interval_days}
            onChange={(e) => onChange({ ...value, interval_days: Number(e.target.value) })}
            style={{ ...inputStyle, width: 110 }}
          />
        </div>
        <div>
          <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
            Ultima volta fatta
          </label>
          <input
            type="date"
            value={value.last_done_date ?? ''}
            onChange={(e) => onChange({ ...value, last_done_date: e.target.value || null })}
            style={inputStyle}
          />
        </div>
        <div>
          <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
            Per chi (facoltativo)
          </label>
          <input
            value={value.assignee ?? ''}
            onChange={(e) => onChange({ ...value, assignee: e.target.value })}
            placeholder="Es. Marco"
            style={inputStyle}
          />
        </div>
      </div>
      <input
        value={value.notes ?? ''}
        onChange={(e) => onChange({ ...value, notes: e.target.value })}
        placeholder="Note (facoltative)"
        style={inputStyle}
      />
    </div>
  )
}
