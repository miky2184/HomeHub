import { useEffect, useState } from 'react'
import { CalendarClock, ChefHat, Cookie, Settings } from 'lucide-react'
import type { SchoolMenuTemplateEntry, SnackTemplateEntry } from '../api/types'
import { useMenuSettings, useUpsertSchoolAnchor, useUpsertSchoolTemplate, useUpsertSnacks } from '../api/hooks'
import { Card } from '../components/Card'
import { DAY_LABELS } from '../lib/date'
import { buttonStyle, inputStyle } from '../styles/controls'

const CYCLE_WEEKS = [1, 2, 3, 4]
const WEEKDAY_LABELS = DAY_LABELS.slice(0, 5)
const SNACK_TYPES: Array<{ key: SnackTemplateEntry['snack_type']; label: string }> = [
  { key: 'mattina', label: 'Mattina' },
  { key: 'pomeriggio', label: 'Pomeriggio' },
]

/** Impostazioni previste in futuro: nome membro famiglia, città meteo, ecc.
 * Per ora: data entry del menu scuola e delle merende — cose "spot" (2
 * volte l'anno per il menu, occasionale per le merende), non pensate per
 * essere modificate dalle pagine di uso quotidiano (Home/Cucina, sola
 * lettura) — vedi ARCHITECTURE.md. */
export function SettingsPage() {
  const { data: menuSettings, isLoading } = useMenuSettings()
  const upsertTemplate = useUpsertSchoolTemplate()
  const upsertAnchor = useUpsertSchoolAnchor()
  const upsertSnacks = useUpsertSnacks()

  const [template, setTemplate] = useState<Record<string, string>>({})
  const [anchorMonday, setAnchorMonday] = useState('')
  const [anchorWeek, setAnchorWeek] = useState(1)
  const [snacks, setSnacks] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!menuSettings) return

    const t: Record<string, string> = {}
    menuSettings.school_template.forEach((e) => {
      t[`${e.cycle_week}-${e.day_of_week}`] = e.meal_text
    })
    setTemplate(t)

    if (menuSettings.cycle_anchor) {
      setAnchorMonday(menuSettings.cycle_anchor.anchor_monday)
      setAnchorWeek(menuSettings.cycle_anchor.anchor_cycle_week)
    }

    const s: Record<string, string> = {}
    menuSettings.snacks.forEach((e) => {
      s[`${e.day_of_week}-${e.snack_type}`] = e.snack_text
    })
    setSnacks(s)
  }, [menuSettings])

  function saveTemplate() {
    const entries: SchoolMenuTemplateEntry[] = []
    CYCLE_WEEKS.forEach((week) => {
      WEEKDAY_LABELS.forEach((_, dayIndex) => {
        const text = template[`${week}-${dayIndex}`]?.trim()
        if (text) entries.push({ cycle_week: week, day_of_week: dayIndex, meal_text: text })
      })
    })
    upsertTemplate.mutate(entries)
  }

  function saveAnchor() {
    if (!anchorMonday) return
    upsertAnchor.mutate({ anchor_monday: anchorMonday, anchor_cycle_week: anchorWeek })
  }

  function saveSnacks() {
    const entries: SnackTemplateEntry[] = []
    SNACK_TYPES.forEach(({ key }) => {
      WEEKDAY_LABELS.forEach((_, dayIndex) => {
        const text = snacks[`${dayIndex}-${key}`]?.trim()
        if (text) entries.push({ day_of_week: dayIndex, snack_type: key, snack_text: text })
      })
    })
    upsertSnacks.mutate(entries)
  }

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Impostazioni</h1>

      <Card label="Punto di partenza del ciclo scuola" icon={CalendarClock} category="cucina">
        <p style={{ margin: '0 0 10px', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
          "Da questo lunedì si parte dalla settimana N" — aggiornalo solo quando la scuola comunica un nuovo
          volantino (di solito 2 volte l'anno). Seleziona un lunedì.
        </p>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
          <input
            type="date"
            value={anchorMonday}
            onChange={(e) => setAnchorMonday(e.target.value)}
            style={inputStyle}
          />
          <select value={anchorWeek} onChange={(e) => setAnchorWeek(Number(e.target.value))} style={inputStyle}>
            {CYCLE_WEEKS.map((w) => (
              <option key={w} value={w}>
                Settimana {w}
              </option>
            ))}
          </select>
          <button style={buttonStyle} onClick={saveAnchor}>
            Salva
          </button>
        </div>
      </Card>

      <Card label="Menu scuola (rotazione 4 settimane)" icon={ChefHat} category="cucina">
        {isLoading ? (
          <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>
        ) : (
          <>
            {CYCLE_WEEKS.map((week) => (
              <div key={week} style={{ marginBottom: 14 }}>
                <p
                  style={{
                    margin: '0 0 6px',
                    fontSize: 'var(--fs-label)',
                    fontWeight: 700,
                    color: 'var(--cat-cucina-fg)',
                  }}
                >
                  Settimana {week}
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 8 }}>
                  {WEEKDAY_LABELS.map((label, dayIndex) => (
                    <div key={dayIndex}>
                      <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>{label}</label>
                      <textarea
                        value={template[`${week}-${dayIndex}`] ?? ''}
                        onChange={(e) => setTemplate((t) => ({ ...t, [`${week}-${dayIndex}`]: e.target.value }))}
                        placeholder={'Una portata per riga, es.\nPasta al pomodoro\nPolpette\nSpinaci\nFrutta'}
                        rows={4}
                        style={{ ...inputStyle, width: '100%', resize: 'vertical', fontFamily: 'inherit' }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}
            <button style={buttonStyle} onClick={saveTemplate}>
              Salva menu scuola
            </button>
          </>
        )}
      </Card>

      <Card label="Merende (fisse per giorno della settimana)" icon={Cookie} category="cucina">
        {isLoading ? (
          <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>
        ) : (
          <>
            {SNACK_TYPES.map(({ key, label }) => (
              <div key={key} style={{ marginBottom: 14 }}>
                <p
                  style={{
                    margin: '0 0 6px',
                    fontSize: 'var(--fs-label)',
                    fontWeight: 700,
                    color: 'var(--cat-cucina-fg)',
                  }}
                >
                  {label}
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 8 }}>
                  {WEEKDAY_LABELS.map((dayLabel, dayIndex) => (
                    <div key={dayIndex}>
                      <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>{dayLabel}</label>
                      <input
                        value={snacks[`${dayIndex}-${key}`] ?? ''}
                        onChange={(e) => setSnacks((s) => ({ ...s, [`${dayIndex}-${key}`]: e.target.value }))}
                        placeholder="Es. Yogurt e cereali"
                        style={{ ...inputStyle, width: '100%' }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}
            <button style={buttonStyle} onClick={saveSnacks}>
              Salva merende
            </button>
          </>
        )}
      </Card>

      <Card label="Altre impostazioni" icon={Settings} category="home">
        <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-secondary)' }}>
          In arrivo: nome di famiglia, città meteo, credenziali integrazioni.
        </p>
      </Card>
    </>
  )
}
