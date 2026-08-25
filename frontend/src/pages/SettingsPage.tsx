import { useEffect, useState } from 'react'
import { Calendar, CalendarClock, ChefHat, CloudSun, Cookie, Home, Palette, Plug, ShoppingBasket, ShoppingCart, Users, Watch } from 'lucide-react'
import type { SchoolMenuTemplateEntry, SnackTemplateEntry } from '../api/types'
import {
  useAppSettings,
  useMenuSettings,
  useUpdateAppSettings,
  useUpsertSchoolAnchor,
  useUpsertSchoolTemplate,
  useUpsertSnacks,
} from '../api/hooks'
import { Card } from '../components/Card'
import { DAY_LABELS } from '../lib/date'
import { BACKGROUND_PALETTE, DEFAULT_BACKGROUND_THEME } from '../lib/palette'
import { buttonStyle, ghostButtonStyle, inputStyle } from '../styles/controls'
import { CATEGORY_COLORS, type Category } from '../styles/categories'

const CYCLE_WEEKS = [1, 2, 3, 4]
const WEEKDAY_LABELS = DAY_LABELS.slice(0, 5)
const SNACK_TYPES: Array<{ key: SnackTemplateEntry['snack_type']; label: string }> = [
  { key: 'mattina', label: 'Mattina' },
  { key: 'pomeriggio', label: 'Pomeriggio' },
]

const TABS: Array<{ key: string; label: string; icon: typeof Home; category: Category }> = [
  { key: 'famiglia', label: 'Famiglia & Aspetto', icon: Home, category: 'home' },
  { key: 'meteo', label: 'Meteo', icon: CloudSun, category: 'agenda' },
  { key: 'menu', label: 'Menu scuola', icon: ChefHat, category: 'cucina' },
  { key: 'integrazioni', label: 'Integrazioni', icon: Plug, category: 'evidenza' },
]

// Stato di un campo segreto (password/token): mai pre-compilato col valore
// vero (il backend non lo rimanda mai, vedi AppSettings.*_set) — solo un
// draft di ciò che l'utente sta digitando ora, più un flag "clear" per
// l'azione esplicita "ripristina .env" (che altrimenti, a campo vuoto,
// verrebbe interpretata come "non toccare", vedi useUpdateAppSettings).
interface SecretDraft {
  value: string
  clear: boolean
}
const EMPTY_SECRET: SecretDraft = { value: '', clear: false }

function secretPayload(field: string, draft: SecretDraft): Record<string, string> {
  if (draft.clear) return { [field]: '' }
  if (draft.value.trim()) return { [field]: draft.value.trim() }
  return {}
}

function SecretField({
  label,
  isSet,
  draft,
  onChange,
}: {
  label: string
  isSet: boolean
  draft: SecretDraft
  onChange: (next: SecretDraft) => void
}) {
  return (
    <div>
      <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>{label}</label>
      <div style={{ display: 'flex', gap: 8 }}>
        <input
          type="password"
          value={draft.value}
          onChange={(e) => onChange({ value: e.target.value, clear: false })}
          placeholder={
            draft.clear
              ? 'Verrà rimosso al salvataggio → torna a .env'
              : isSet
                ? '••••••• (lascia vuoto per non modificare)'
                : 'Non impostato — usa .env'
          }
          style={{ ...inputStyle, flex: 1 }}
        />
        {isSet && !draft.clear && (
          <button type="button" onClick={() => onChange({ value: '', clear: true })} style={ghostButtonStyle}>
            Ripristina .env
          </button>
        )}
        {draft.clear && (
          <button type="button" onClick={() => onChange(EMPTY_SECRET)} style={ghostButtonStyle}>
            Annulla
          </button>
        )}
      </div>
    </div>
  )
}

function TabButton({
  tab,
  active,
  onClick,
}: {
  tab: (typeof TABS)[number]
  active: boolean
  onClick: () => void
}) {
  const colors = CATEGORY_COLORS[tab.category]
  const Icon = tab.icon
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '10px 16px',
        borderRadius: 'var(--radius-control)',
        border: '1px solid ' + (active ? colors.fg : 'var(--border)'),
        background: active ? colors.bg : 'var(--bg-card)',
        color: active ? colors.fg : 'var(--text-secondary)',
        fontSize: 'var(--fs-label)',
        fontWeight: 700,
        cursor: 'pointer',
        whiteSpace: 'nowrap',
      }}
    >
      <Icon size={16} />
      {tab.label}
    </button>
  )
}

/** Impostazioni organizzate a sezioni (una tab alla volta) invece di un
 * unico lungo elenco di card — con la famiglia (nome, aspetto), il meteo,
 * il menu scuola e le credenziali delle integrazioni tutte insieme in
 * piano non si trovava più niente. */
export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<string>('famiglia')

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Impostazioni</h1>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 4 }}>
        {TABS.map((tab) => (
          <TabButton key={tab.key} tab={tab} active={activeTab === tab.key} onClick={() => setActiveTab(tab.key)} />
        ))}
      </div>

      {activeTab === 'famiglia' && <FamigliaAspettoSection />}
      {activeTab === 'meteo' && <MeteoSection />}
      {activeTab === 'menu' && <MenuScuolaSection />}
      {activeTab === 'integrazioni' && <IntegrazioniSection />}
    </>
  )
}

function FamigliaAspettoSection() {
  const { data: appSettings, isLoading } = useAppSettings()
  const updateSettings = useUpdateAppSettings()
  const [familyName, setFamilyName] = useState('')
  const [shoppingLimit, setShoppingLimit] = useState('')

  useEffect(() => {
    if (!appSettings) return
    setFamilyName(appSettings.family_name)
    setShoppingLimit(String(appSettings.shopping_preview_limit))
  }, [appSettings])

  const currentTheme = appSettings?.background_theme || DEFAULT_BACKGROUND_THEME

  return (
    <>
      <Card label="Nome famiglia" icon={Users} category="home">
        <p style={{ margin: '0 0 10px', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
          Mostrato nel saluto in Home, es. "Buongiorno — Famiglia Micunco".
        </p>
        {isLoading ? (
          <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>
        ) : (
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <input
              value={familyName}
              onChange={(e) => setFamilyName(e.target.value)}
              placeholder="Es. Famiglia Micunco"
              style={{ ...inputStyle, flex: 1, minWidth: 220 }}
            />
            <button style={buttonStyle} onClick={() => updateSettings.mutate({ family_name: familyName.trim() })}>
              Salva
            </button>
          </div>
        )}
      </Card>

      <Card label="Lista della spesa in Home" icon={ShoppingBasket} category="home">
        <p style={{ margin: '0 0 10px', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
          Quanti prodotti mostrare in anteprima nella card "Lista della spesa" in Home.
        </p>
        {isLoading ? (
          <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>
        ) : (
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <input
              type="number"
              min={0}
              max={20}
              value={shoppingLimit}
              onChange={(e) => setShoppingLimit(e.target.value)}
              style={{ ...inputStyle, width: 90 }}
            />
            <button
              style={buttonStyle}
              onClick={() =>
                updateSettings.mutate({
                  shopping_preview_limit: shoppingLimit.trim() ? Number(shoppingLimit) : null,
                })
              }
            >
              Salva
            </button>
          </div>
        )}
      </Card>

      <Card label="Sfondo" icon={Palette} category="home">
        <p style={{ margin: '0 0 12px', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
          Scegli un colore per lo sfondo dell'app — si applica subito.
        </p>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          {Object.entries(BACKGROUND_PALETTE).map(([key, theme]) => (
            <button
              key={key}
              onClick={() => updateSettings.mutate({ background_theme: key === DEFAULT_BACKGROUND_THEME ? '' : key })}
              title={theme.label}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 6,
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: 4,
              }}
            >
              <span
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: '50%',
                  background: theme.bgPage,
                  border: currentTheme === key ? '3px solid var(--accent)' : '2px solid var(--border-strong)',
                  boxShadow: 'inset 0 0 0 8px ' + theme.bgRail,
                }}
              />
              <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{theme.label}</span>
            </button>
          ))}
        </div>
      </Card>
    </>
  )
}

function MeteoSection() {
  const { data: appSettings, isLoading } = useAppSettings()
  const updateSettings = useUpdateAppSettings()
  const [city, setCity] = useState('')
  const [lat, setLat] = useState('')
  const [lon, setLon] = useState('')

  useEffect(() => {
    if (!appSettings) return
    setCity(appSettings.weather_city)
    setLat(appSettings.weather_latitude?.toString() ?? '')
    setLon(appSettings.weather_longitude?.toString() ?? '')
  }, [appSettings])

  function save() {
    updateSettings.mutate({
      weather_city: city.trim(),
      weather_latitude: lat.trim() ? Number(lat) : null,
      weather_longitude: lon.trim() ? Number(lon) : null,
    })
  }

  return (
    <Card label="Meteo" icon={CloudSun} category="agenda">
      <p style={{ margin: '0 0 12px', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
        Latitudine/longitudine hanno la priorità (coordinate esatte di casa, niente geocoding); se le lasci
        vuote si usa il nome per individuare la posizione.
      </p>
      {isLoading ? (
        <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>
      ) : (
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
              Nome da visualizzare
            </label>
            <input value={city} onChange={(e) => setCity(e.target.value)} placeholder="Es. Milano" style={inputStyle} />
          </div>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
              Latitudine
            </label>
            <input
              value={lat}
              onChange={(e) => setLat(e.target.value)}
              placeholder="Es. 45.4642"
              inputMode="decimal"
              style={{ ...inputStyle, width: 140 }}
            />
          </div>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
              Longitudine
            </label>
            <input
              value={lon}
              onChange={(e) => setLon(e.target.value)}
              placeholder="Es. 9.19"
              inputMode="decimal"
              style={{ ...inputStyle, width: 140 }}
            />
          </div>
          <button style={buttonStyle} onClick={save}>
            Salva
          </button>
        </div>
      )}
    </Card>
  )
}

function IntegrazioniSection() {
  const { data: appSettings, isLoading } = useAppSettings()
  const updateSettings = useUpdateAppSettings()

  const [googleClientId, setGoogleClientId] = useState('')
  const [googleCalendarIds, setGoogleCalendarIds] = useState('')
  const [googleClientSecret, setGoogleClientSecret] = useState<SecretDraft>(EMPTY_SECRET)
  const [googleRefreshToken, setGoogleRefreshToken] = useState<SecretDraft>(EMPTY_SECRET)

  const [bringEmail, setBringEmail] = useState('')
  const [bringPassword, setBringPassword] = useState<SecretDraft>(EMPTY_SECRET)

  const [garminEmail, setGarminEmail] = useState('')
  const [garminPassword, setGarminPassword] = useState<SecretDraft>(EMPTY_SECRET)

  useEffect(() => {
    if (!appSettings) return
    setGoogleClientId(appSettings.google_client_id)
    setGoogleCalendarIds(appSettings.google_calendar_ids.join(', '))
    setBringEmail(appSettings.bring_email)
    setGarminEmail(appSettings.garmin_email)
  }, [appSettings])

  function saveGoogle() {
    const calendarIds = googleCalendarIds.trim()
      ? googleCalendarIds.split(',').map((s) => s.trim()).filter(Boolean)
      : null
    updateSettings.mutate(
      {
        google_client_id: googleClientId.trim(),
        google_calendar_ids: calendarIds,
        ...secretPayload('google_client_secret', googleClientSecret),
        ...secretPayload('google_refresh_token', googleRefreshToken),
      },
      { onSuccess: () => { setGoogleClientSecret(EMPTY_SECRET); setGoogleRefreshToken(EMPTY_SECRET) } }
    )
  }

  function saveBring() {
    updateSettings.mutate(
      { bring_email: bringEmail.trim(), ...secretPayload('bring_password', bringPassword) },
      { onSuccess: () => setBringPassword(EMPTY_SECRET) }
    )
  }

  function saveGarmin() {
    updateSettings.mutate(
      { garmin_email: garminEmail.trim(), ...secretPayload('garmin_password', garminPassword) },
      { onSuccess: () => setGarminPassword(EMPTY_SECRET) }
    )
  }

  if (isLoading || !appSettings) {
    return (
      <Card label="Integrazioni" icon={Plug} category="evidenza">
        <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>
      </Card>
    )
  }

  return (
    <>
      <p style={{ margin: '0 0 12px', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
        Se compilate qui, queste credenziali vincono su quelle in <code>.env</code> sul NUC — utile per
        cambiarle senza accedere al server. Lasciando un campo vuoto resta quanto già in <code>.env</code>.
      </p>

      <Card label="Google Calendar" icon={Calendar} category="evidenza">
        <div style={{ display: 'grid', gap: 12 }}>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
              Client ID
            </label>
            <input value={googleClientId} onChange={(e) => setGoogleClientId(e.target.value)} style={{ ...inputStyle, width: '100%' }} />
          </div>
          <SecretField
            label="Client secret"
            isSet={appSettings.google_client_secret_set}
            draft={googleClientSecret}
            onChange={setGoogleClientSecret}
          />
          <SecretField
            label="Refresh token"
            isSet={appSettings.google_refresh_token_set}
            draft={googleRefreshToken}
            onChange={setGoogleRefreshToken}
          />
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
              Calendari (ID separati da virgola)
            </label>
            <input
              value={googleCalendarIds}
              onChange={(e) => setGoogleCalendarIds(e.target.value)}
              placeholder="primary, famiglia@group.calendar.google.com"
              style={{ ...inputStyle, width: '100%' }}
            />
          </div>
          <button style={{ ...buttonStyle, justifySelf: 'start' }} onClick={saveGoogle}>
            Salva Google Calendar
          </button>
        </div>
      </Card>

      <Card label="Bring!" icon={ShoppingCart} category="evidenza">
        <div style={{ display: 'grid', gap: 12 }}>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Email</label>
            <input value={bringEmail} onChange={(e) => setBringEmail(e.target.value)} style={{ ...inputStyle, width: '100%' }} />
          </div>
          <SecretField label="Password" isSet={appSettings.bring_password_set} draft={bringPassword} onChange={setBringPassword} />
          <button style={{ ...buttonStyle, justifySelf: 'start' }} onClick={saveBring}>
            Salva Bring!
          </button>
        </div>
      </Card>

      <Card label="Garmin Connect" icon={Watch} category="evidenza">
        <div style={{ display: 'grid', gap: 12 }}>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Email</label>
            <input value={garminEmail} onChange={(e) => setGarminEmail(e.target.value)} style={{ ...inputStyle, width: '100%' }} />
          </div>
          <SecretField label="Password" isSet={appSettings.garmin_password_set} draft={garminPassword} onChange={setGarminPassword} />
          <p style={{ margin: 0, fontSize: 11, color: 'var(--text-muted)' }}>
            Dopo aver cambiato le credenziali va comunque rieseguito una tantum <code>backend/scripts/garmin_login_setup.py</code>{' '}
            se Garmin richiede un MFA al login (non gestibile da qui, serve un terminale interattivo).
          </p>
          <button style={{ ...buttonStyle, justifySelf: 'start' }} onClick={saveGarmin}>
            Salva Garmin Connect
          </button>
        </div>
      </Card>
    </>
  )
}

function MenuScuolaSection() {
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
    </>
  )
}
