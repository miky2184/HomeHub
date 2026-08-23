import { CalendarDays, ChefHat, Dumbbell, House, ShoppingBasket, Sun } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useHomeSummary, useMarkTrainingDone, useToggleShoppingItem } from '../api/hooks'
import { Card } from '../components/Card'
import { FAMILY_MEMBER_NAME, getGreeting } from '../config'
import { useClock } from '../hooks/useClock'
import { inferEventIcon } from '../lib/eventIcon'
import { currentWeekStart } from '../lib/date'
import { CATEGORY_COLORS } from '../styles/categories'

export function HomePage() {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useHomeSummary()
  const toggleShoppingItem = useToggleShoppingItem()
  const markTrainingDone = useMarkTrainingDone(currentWeekStart())
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
            {getGreeting(now)} {FAMILY_MEMBER_NAME}!
          </h1>
          <p style={{ margin: '6px 0 0', color: 'var(--text-secondary)', fontSize: 'var(--fs-body)' }}>
            Ecco cosa c'è oggi in casa.
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <p style={{ margin: 0, fontSize: 'var(--fs-clock)', fontWeight: 700, color: 'var(--text-primary)' }}>{time}</p>
          <p style={{ margin: '2px 0 0', fontSize: 'var(--fs-date)', color: 'var(--cat-home-fg)', fontWeight: 700, textTransform: 'uppercase' }}>
            {date}
          </p>
          {data.weather?.temperature_c != null && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'flex-end', marginTop: 6, color: 'var(--text-secondary)' }}>
              <Sun size={20} />
              <span style={{ fontSize: 'var(--fs-heading)', fontWeight: 700 }}>{Math.round(data.weather.temperature_c)}°</span>
            </div>
          )}
        </div>
      </div>

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
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--gap-md)' }}>
        <Card label="Menu di casa" icon={ChefHat} category="cucina" footerLabel="Vedi menu completo" onFooterClick={() => navigate('/menu')}>
          <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-primary)' }}>
            {data.today_menu?.home_meal ?? 'Da definire'}
          </p>
        </Card>

        <Card label="Menu scuola" icon={ChefHat} category="scuola" footerLabel="Vedi menu mensa" onFooterClick={() => navigate('/menu')}>
          <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-primary)' }}>
            {data.today_menu?.school_meal ?? 'Da definire'}
          </p>
        </Card>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--gap-md)' }}>
        <Card label="Lista della spesa" icon={ShoppingBasket} category="spesa" footerLabel="Vedi lista" onFooterClick={() => navigate('/spesa')}>
          <p style={{ margin: 0, fontSize: 32, fontWeight: 700, color: 'var(--cat-spesa-fg)' }}>{data.shopping_total_count}</p>
          <p style={{ margin: '2px 0 0', fontSize: 'var(--fs-label)', color: 'var(--text-secondary)' }}>prodotti da comprare</p>
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
            {data.inventory_alerts.length > 0 ? 'scorte in esaurimento' : 'tutto a posto'}
          </p>
        </Card>
      </div>

      {data.next_training && (
        <Card label="Prossimo allenamento" icon={Dumbbell} category="attivita" footerLabel="Vedi allenamenti" onFooterClick={() => navigate('/allenamenti')}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-primary)' }}>{data.next_training.session_text}</p>
            <button
              onClick={(e) => {
                e.stopPropagation()
                markTrainingDone.mutate({ id: data.next_training!.id, done: true })
              }}
              aria-label="Segna come fatto"
              style={{
                background: 'var(--cat-attivita-bg)',
                border: 'none',
                color: 'var(--cat-attivita-fg)',
                borderRadius: '50%',
                width: 36,
                height: 36,
                cursor: 'pointer',
                fontWeight: 700,
              }}
            >
              ✓
            </button>
          </div>
        </Card>
      )}

      {data.shopping_preview.length > 0 && (
        <Card label="Da comprare" icon={ShoppingBasket} category="spesa">
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
        </Card>
      )}
    </>
  )
}
