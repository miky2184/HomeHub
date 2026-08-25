import { CalendarDays, CheckSquare, ChefHat, Check, Dumbbell, House, ShoppingBasket, Wrench } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { HomeMeals } from '../api/types'
import { useHomeSummary, useMarkTrainingDone, useToggleShoppingItem, useUpdateChore } from '../api/hooks'
import { Card } from '../components/Card'
import { MealList } from '../components/MealList'
import { WeatherCard } from '../components/WeatherCard'
import { getGreeting } from '../config'
import { useClock } from '../hooks/useClock'
import { choreDueInfo } from '../lib/chores'
import { inferEventIcon } from '../lib/eventIcon'
import { currentWeekStart, dateFromWeek, relativeDayLabel, toDateKey } from '../lib/date'
import { dueDateInfo, PRIORITY_META } from '../lib/todo'
import { CATEGORY_COLORS } from '../styles/categories'

// Ordine cronologico della giornata: la figlia pranza a scuola (school_meal,
// altra card), ma gli adulti in casa fanno tutti questi pasti — mostriamo
// solo quelli che hanno davvero un piano quel giorno, per tenere la card
// compatta quando è pianificata solo la cena.
const HOME_MEAL_LABELS: { key: keyof HomeMeals; label: string }[] = [
  { key: 'breakfast', label: 'Colazione' },
  { key: 'snack_morning', label: 'Spuntino mattina' },
  { key: 'lunch', label: 'Pranzo' },
  { key: 'snack_afternoon', label: 'Spuntino pomeriggio' },
  { key: 'dinner', label: 'Cena' },
  { key: 'snack_evening', label: 'Spuntino sera' },
]

function HomeMealsList({ meals }: { meals: HomeMeals | undefined }) {
  const present = HOME_MEAL_LABELS.filter(({ key }) => meals?.[key])
  if (present.length === 0) {
    return <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-primary)' }}>Da definire</p>
  }
  return (
    <>
      {present.map(({ key, label }, i) => (
        <div key={key} style={{ marginTop: i > 0 ? 10 : 0 }}>
          <p style={{ margin: '0 0 2px', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>{label}</p>
          <MealList text={meals![key]!} />
        </div>
      ))}
    </>
  )
}

export function HomePage() {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useHomeSummary()
  const toggleShoppingItem = useToggleShoppingItem()
  const markTrainingDone = useMarkTrainingDone(currentWeekStart())
  const updateChore = useUpdateChore()
  const { now, time, date } = useClock()

  if (isLoading) return <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>
  if (isError || !data) {
    return <p style={{ color: 'var(--danger)' }}>Impossibile caricare i dati dal backend.</p>
  }

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 'var(--fs-greeting)', color: 'var(--text-primary)' }}>
            {getGreeting(now)}
            {data.family_name && (
              <span style={{ color: 'var(--text-secondary)', fontWeight: 400 }}> — {data.family_name}</span>
            )}
          </h1>
          <p style={{ margin: '6px 0 0', color: 'var(--text-secondary)', fontSize: 'var(--fs-body)' }}>
            {data.saint_of_day && `Oggi è ${data.saint_of_day}`}
            {data.saint_of_day && data.quote_of_day && ' · '}
            {data.quote_of_day && `"${data.quote_of_day}"`}
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <p style={{ margin: 0, fontSize: 'var(--fs-clock)', fontWeight: 700, color: 'var(--text-primary)' }}>{time}</p>
          <p style={{ margin: '2px 0 0', fontSize: 'var(--fs-date)', color: 'var(--cat-home-fg)', fontWeight: 700, textTransform: 'uppercase' }}>
            {date}
          </p>
        </div>
      </div>

      {data.weather && <WeatherCard weather={data.weather} />}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--gap-md)' }}>
        <Card
          label="Oggi"
          icon={CalendarDays}
          category="agenda"
          footerLabel="Vedi tutti gli eventi"
          onFooterClick={() => navigate('/calendario')}
        >
          {data.today_events.length === 0 ? (
            <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-secondary)' }}>
              Nessun evento in programma
            </p>
          ) : (
            data.today_events.map((event) => {
              const { Icon, category } = inferEventIcon(event.title)
              const colors = CATEGORY_COLORS[category]
              return (
                <div key={event.id} style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                  <span style={{ width: 30, height: 30, borderRadius: '50%', background: colors.bg, color: colors.fg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Icon size={16} />
                  </span>
                  <span style={{ fontSize: 'var(--fs-body)', color: 'var(--text-secondary)', width: 56, flexShrink: 0 }}>
                    {new Intl.DateTimeFormat('it-IT', { hour: '2-digit', minute: '2-digit' }).format(new Date(event.start))}
                  </span>
                  <span style={{ fontSize: 'var(--fs-body)', color: 'var(--text-primary)', fontWeight: 600 }}>{event.title}</span>
                </div>
              )
            })
          )}

          {data.next_training && (
            <>
              <div style={{ borderTop: '1px solid var(--border)', margin: '10px 0' }} />
              <div
                onClick={() => navigate('/allenamenti')}
                style={{ display: 'flex', gap: 12, alignItems: 'center', cursor: 'pointer' }}
              >
                <span
                  style={{
                    width: 30,
                    height: 30,
                    borderRadius: '50%',
                    background: 'var(--cat-attivita-bg)',
                    color: 'var(--cat-attivita-fg)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <Dumbbell size={16} />
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <span style={{ fontSize: 'var(--fs-body)', color: 'var(--text-primary)', fontWeight: 600 }}>
                    {data.next_training.session_text}
                  </span>
                  <p style={{ margin: 0, fontSize: 'var(--fs-label)', color: 'var(--text-secondary)' }}>
                    {relativeDayLabel(dateFromWeek(data.next_training.week_start_date, data.next_training.day_of_week))}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    markTrainingDone.mutate({ id: data.next_training!.id, done: true })
                  }}
                  aria-label="Segna allenamento come fatto"
                  style={{
                    background: 'var(--cat-attivita-bg)',
                    border: 'none',
                    color: 'var(--cat-attivita-fg)',
                    borderRadius: '50%',
                    width: 36,
                    height: 36,
                    cursor: 'pointer',
                    fontWeight: 700,
                    flexShrink: 0,
                  }}
                >
                  ✓
                </button>
              </div>
            </>
          )}
        </Card>

        <Card
          label={`Da fare · ${data.todos.pending_count}`}
          icon={CheckSquare}
          category="todo"
          footerLabel="Vedi tutti"
          onFooterClick={() => navigate('/todo')}
        >
          {data.todos.top.length === 0 ? (
            <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-secondary)' }}>
              Nessun todo da fare
            </p>
          ) : (
            data.todos.top.map((todo) => {
              const due = dueDateInfo(todo.due_date)
              const priority = PRIORITY_META[todo.priority]
              return (
                <div key={todo.id} style={{ display: 'flex', gap: 10, alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                  <span style={{ width: 10, height: 10, borderRadius: '50%', background: priority.color, flexShrink: 0 }} />
                  <span style={{ fontSize: 'var(--fs-body)', color: 'var(--text-primary)', fontWeight: 600, flex: 1, minWidth: 0 }}>
                    {todo.title}
                  </span>
                  {due && (
                    <span
                      style={{
                        fontSize: 'var(--fs-label)',
                        fontWeight: due.overdue ? 700 : 400,
                        color: due.overdue ? 'var(--danger)' : 'var(--text-muted)',
                        flexShrink: 0,
                      }}
                    >
                      {due.label}
                    </span>
                  )}
                </div>
              )
            })
          )}
        </Card>
      </div>

      {data.chores.due_count > 0 && (
        <Card
          label={`Manutenzione · ${data.chores.due_count}`}
          icon={Wrench}
          category="manutenzione"
          footerLabel="Vedi tutte"
          onFooterClick={() => navigate('/manutenzione')}
        >
          {data.chores.top.map((chore) => {
            const due = choreDueInfo(chore)
            return (
              <div key={chore.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <span style={{ fontSize: 'var(--fs-body)', color: 'var(--text-primary)', fontWeight: 600 }}>
                    {chore.title}
                  </span>
                  <p style={{ margin: 0, fontSize: 'var(--fs-label)', fontWeight: due.overdue ? 700 : 400, color: due.overdue ? 'var(--danger)' : 'var(--text-secondary)' }}>
                    {due.label}
                  </p>
                </div>
                <button
                  onClick={() => updateChore.mutate({ id: chore.id, last_done_date: toDateKey(new Date()) })}
                  aria-label={`Segna "${chore.title}" come fatta oggi`}
                  title="Fatto oggi"
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: '50%',
                    border: 'none',
                    background: 'var(--cat-manutenzione-bg)',
                    color: 'var(--cat-manutenzione-fg)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    flexShrink: 0,
                  }}
                >
                  <Check size={16} />
                </button>
              </div>
            )
          })}
        </Card>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--gap-md)' }}>
        <Card
          label={`Menu di casa · ${menuDayLabel(data.today_menu?.date)}`}
          icon={ChefHat}
          category="cucina"
          footerLabel="Vedi menu completo"
          onFooterClick={() => navigate('/menu')}
        >
          <HomeMealsList meals={data.today_menu?.home_meals} />
        </Card>

        <Card
          label={`Menu scuola · ${menuDayLabel(data.today_menu?.date)}`}
          icon={ChefHat}
          category="scuola"
          footerLabel="Vedi menu mensa"
          onFooterClick={() => navigate('/menu')}
        >
          {data.today_menu?.school_meal ? (
            <MealList text={data.today_menu.school_meal} />
          ) : (
            <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-primary)' }}>Da definire</p>
          )}
          {(data.today_menu?.snack_morning || data.today_menu?.snack_afternoon) && (
            <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--border)' }}>
              <p style={{ margin: 0, fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
                Merenda mattina: <span style={{ color: 'var(--text-primary)' }}>{data.today_menu?.snack_morning ?? '—'}</span>
              </p>
              <p style={{ margin: '4px 0 0', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
                Merenda pomeriggio:{' '}
                <span style={{ color: 'var(--text-primary)' }}>{data.today_menu?.snack_afternoon ?? '—'}</span>
              </p>
            </div>
          )}
        </Card>
      </div>

      <Card label="Lista della spesa" icon={ShoppingBasket} category="spesa" footerLabel="Vedi lista" onFooterClick={() => navigate('/spesa')}>
        <p style={{ margin: 0, fontSize: 32, fontWeight: 700, color: 'var(--cat-spesa-fg)' }}>{data.shopping_total_count}</p>
        <p style={{ margin: '2px 0 0', fontSize: 'var(--fs-label)', color: 'var(--text-secondary)' }}>prodotti da comprare</p>

        {data.shopping_preview.length > 0 && (
          <>
            <div style={{ borderTop: '1px solid var(--border)', margin: '14px 0 10px' }} />
            {data.shopping_preview.map((item) => (
              <label key={item.id} style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '6px 0', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={item.checked}
                  onChange={() => toggleShoppingItem.mutate(item.id)}
                  style={{ width: 20, height: 20 }}
                />
                <span style={{ fontSize: 'var(--fs-body)', color: 'var(--text-primary)' }}>{item.name}</span>
              </label>
            ))}
          </>
        )}
      </Card>

      <Card
        label="Casa"
        icon={House}
        category="casa"
        variant={data.inventory_alerts.length > 0 ? 'warning' : 'default'}
        footerLabel="Vedi tutto"
        onFooterClick={() => navigate('/inventory')}
      >
        <p style={{ margin: 0, fontSize: 32, fontWeight: 700, color: data.inventory_alerts.length > 0 ? 'var(--warning)' : 'var(--cat-casa-fg)' }}>
          {data.inventory_alerts.length}
        </p>
        <p style={{ margin: '2px 0 0', fontSize: 'var(--fs-label)', color: 'var(--text-secondary)' }}>
          {data.inventory_alerts.length > 0 ? 'oggetti in scadenza' : 'niente in scadenza'}
        </p>
      </Card>

    </>
  )
}

function menuDayLabel(menuDate: string | undefined): string {
  if (!menuDate) return 'Oggi'
  return menuDate === toDateKey(new Date()) ? 'Oggi' : 'Domani'
}
