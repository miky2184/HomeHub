import { useState } from 'react'
import { CheckSquare, Pencil, Plus, Trash2 } from 'lucide-react'
import { useCreateTodo, useDeleteTodo, useTodos, useUpdateTodo } from '../api/hooks'
import type { TodoItem, TodoItemInput, TodoPriority } from '../api/types'
import { Card } from '../components/Card'
import { Modal } from '../components/Modal'
import { dueDateInfo, PRIORITY_META, PRIORITY_OPTIONS } from '../lib/todo'
import { buttonStyle, ghostButtonStyle, inputStyle } from '../styles/controls'

const EMPTY_FORM: TodoItemInput = { title: '', assignee: null, priority: 'media', due_date: null }

export function TodoPage() {
  const { data: todos, isLoading } = useTodos(true)
  const createTodo = useCreateTodo()
  const updateTodo = useUpdateTodo()
  const deleteTodo = useDeleteTodo()

  const [form, setForm] = useState<TodoItemInput>(EMPTY_FORM)
  const [showDone, setShowDone] = useState(false)
  const [editing, setEditing] = useState<TodoItem | null>(null)
  const [deleting, setDeleting] = useState<TodoItem | null>(null)

  function handleCreate() {
    if (!form.title.trim()) return
    createTodo.mutate(
      { ...form, title: form.title.trim(), assignee: form.assignee?.trim() || null },
      { onSuccess: () => setForm(EMPTY_FORM) }
    )
  }

  const pendingCount = (todos ?? []).filter((t) => !t.done).length
  const visible = (todos ?? []).filter((t) => showDone || !t.done)

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Todo</h1>

      <Card label="Nuovo todo" icon={Plus} category="todo">
        <TodoFormFields value={form} onChange={setForm} />
        <button style={{ ...buttonStyle, marginTop: 10 }} onClick={handleCreate}>
          Aggiungi
        </button>
      </Card>

      {isLoading && <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>}

      <Card
        label={`Da fare · ${pendingCount}`}
        icon={CheckSquare}
        category="todo"
        footerLabel={showDone ? 'Nascondi completati' : 'Mostra completati'}
        onFooterClick={() => setShowDone((v) => !v)}
      >
        {visible.length === 0 && (
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: 'var(--fs-body)' }}>
            Nessun todo{showDone ? '' : ' da fare'}.
          </p>
        )}
        {visible.map((todo) => {
          const due = dueDateInfo(todo.due_date)
          const priority = PRIORITY_META[todo.priority]
          return (
            <div
              key={todo.id}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 12,
                padding: '10px 0',
                borderBottom: '1px solid var(--border)',
              }}
            >
              <input
                type="checkbox"
                checked={todo.done}
                onChange={() => updateTodo.mutate({ id: todo.id, done: !todo.done })}
                style={{ width: 20, height: 20, marginTop: 2, cursor: 'pointer' }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <p
                  style={{
                    margin: 0,
                    fontSize: 'var(--fs-body)',
                    fontWeight: 600,
                    textDecoration: todo.done ? 'line-through' : 'none',
                    color: todo.done ? 'var(--text-muted)' : 'var(--text-primary)',
                  }}
                >
                  {todo.title}
                </p>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 4 }}>
                  <span style={{ fontSize: 'var(--fs-label)', fontWeight: 700, color: priority.color }}>
                    {priority.label}
                  </span>
                  {todo.assignee && (
                    <span style={{ fontSize: 'var(--fs-label)', color: 'var(--text-secondary)' }}>
                      {todo.assignee}
                    </span>
                  )}
                  {due && (
                    <span
                      style={{
                        fontSize: 'var(--fs-label)',
                        fontWeight: due.overdue ? 700 : 400,
                        color: due.overdue ? 'var(--danger)' : 'var(--text-secondary)',
                      }}
                    >
                      {due.label}
                    </span>
                  )}
                </div>
              </div>
              <button
                aria-label={`Modifica ${todo.title}`}
                onClick={() => setEditing(todo)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <Pencil size={18} />
              </button>
              <button
                aria-label={`Elimina ${todo.title}`}
                onClick={() => setDeleting(todo)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <Trash2 size={18} />
              </button>
            </div>
          )
        })}
      </Card>

      {editing && (
        <Modal title="Modifica todo" onClose={() => setEditing(null)}>
          <TodoFormFields
            value={{
              title: editing.title,
              assignee: editing.assignee,
              priority: editing.priority,
              due_date: editing.due_date,
            }}
            onChange={(next) => setEditing({ ...editing, ...next })}
          />
          <button
            style={{ ...buttonStyle, marginTop: 14, width: '100%' }}
            onClick={() =>
              updateTodo.mutate(
                {
                  id: editing.id,
                  title: editing.title.trim(),
                  assignee: editing.assignee?.trim() || null,
                  priority: editing.priority,
                  due_date: editing.due_date,
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
        <Modal title="Eliminare questo todo?" onClose={() => setDeleting(null)}>
          <p style={{ margin: '0 0 16px', color: 'var(--text-secondary)' }}>
            «{deleting.title}» verrà eliminato definitivamente.
          </p>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
            <button style={ghostButtonStyle} onClick={() => setDeleting(null)}>
              Annulla
            </button>
            <button
              style={{ ...buttonStyle, background: 'var(--danger)' }}
              onClick={() => deleteTodo.mutate(deleting.id, { onSuccess: () => setDeleting(null) })}
            >
              Elimina
            </button>
          </div>
        </Modal>
      )}
    </>
  )
}

function TodoFormFields({ value, onChange }: { value: TodoItemInput; onChange: (value: TodoItemInput) => void }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <input
        value={value.title}
        onChange={(e) => onChange({ ...value, title: e.target.value })}
        placeholder="Cosa c'è da fare?"
        style={inputStyle}
      />
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <select
          value={value.priority}
          onChange={(e) => onChange({ ...value, priority: e.target.value as TodoPriority })}
          style={inputStyle}
        >
          {PRIORITY_OPTIONS.map((p) => (
            <option key={p} value={p}>
              Priorità {PRIORITY_META[p].label}
            </option>
          ))}
        </select>
        <input
          type="date"
          value={value.due_date ?? ''}
          onChange={(e) => onChange({ ...value, due_date: e.target.value || null })}
          style={inputStyle}
        />
        <input
          value={value.assignee ?? ''}
          onChange={(e) => onChange({ ...value, assignee: e.target.value })}
          placeholder="Per chi (facoltativo)"
          style={inputStyle}
        />
      </div>
    </div>
  )
}
