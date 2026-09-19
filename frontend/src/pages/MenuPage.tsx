import type { ComponentType } from 'react'
import { ChefHat, GraduationCap } from 'lucide-react'
import { useMenuWeek } from '../api/hooks'
import { Card } from '../components/Card'
import { MealList } from '../components/MealList'
import { DAY_LABELS, currentWeekStart } from '../lib/date'
import { CATEGORY_COLORS, type Category } from '../styles/categories'

function Section({ label, value }: { label: string; value: string | null }) {
  return (
    <div style={{ marginTop: 10 }}>
      <p style={{ margin: '0 0 4px', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>{label}</p>
      {value ? (
        <MealList text={value} />
      ) : (
        <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-muted)' }}>—</p>
      )}
    </div>
  )
}

// Etichetta sopra, valore sotto (come Section) invece che affiancati: con le
// colonne più strette di prima (Casa/Scuola una accanto all'altra) un
// layout fianco a fianco andava a capo in modo confuso su etichette lunghe
// tipo "Spuntino pomeriggio".
function Row({ label, value }: { label: string; value: string | null }) {
  return (
    <div style={{ padding: '4px 0' }}>
      <p style={{ margin: 0, fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>{label}</p>
      <p style={{ margin: '2px 0 0', fontSize: 'var(--fs-body)', textTransform: value ? 'uppercase' : 'none' }}>
        {value ?? '—'}
      </p>
    </div>
  )
}

// Intestazione di colonna (icona + etichetta nel colore della categoria):
// stesso identico abbinamento icona/colore delle due card "Menu di casa" /
// "Menu scuola" in Home, per riconoscere a colpo d'occhio quale lato è
// quale anche qui, senza dover leggere le etichette dei singoli pasti.
function ColumnHeader({
  label,
  icon: Icon,
  category,
}: {
  label: string
  icon: ComponentType<{ size?: number }>
  category: Category
}) {
  const colors = CATEGORY_COLORS[category]
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
      <span
        aria-hidden
        style={{
          width: 26,
          height: 26,
          borderRadius: '50%',
          background: colors.bg,
          color: colors.fg,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        <Icon size={14} />
      </span>
      <p
        style={{
          margin: 0,
          fontSize: 'var(--fs-label)',
          fontWeight: 700,
          color: colors.fg,
          textTransform: 'uppercase',
          letterSpacing: 0.4,
        }}
      >
        {label}
      </p>
    </div>
  )
}

export function MenuPage() {
  const weekStart = currentWeekStart()
  const { data: week, isLoading, isError } = useMenuWeek(weekStart)

  if (isLoading) return <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>
  if (isError || !week) {
    return (
      <p style={{ color: 'var(--danger)' }}>
        Impossibile caricare il menu (richiede il Postgres configurato in backend/.env).
      </p>
    )
  }

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Cucina — menu della settimana</h1>
      <p style={{ fontSize: 'var(--fs-label)', color: 'var(--text-muted)', margin: '0 0 8px' }}>
        Sola lettura: il menu scuola/merende si aggiorna da Impostazioni (cambia solo un paio di volte l'anno), i
        pasti di casa dall'app dieta.
      </p>

      {/* Due colonne nette, Casa a sinistra / Scuola a destra (stessa
          disposizione — e stessi colori — delle due card gemelle in Home),
          invece di un unico elenco con i pasti dei due mondi interfogliati
          in ordine cronologico: più facile leggere "cosa mangia la bambina
          a scuola" senza dover scremare le righe di casa in mezzo. */}
      {week.days.map((day) => (
        <Card key={day.day_of_week} label={DAY_LABELS[day.day_of_week]} icon={ChefHat} category="cucina">
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: 20 }}>
            <div style={{ borderRight: '1px solid var(--border)', paddingRight: 16 }}>
              <ColumnHeader label="Casa" icon={ChefHat} category="cucina" />
              <Section label="Colazione" value={day.home_meals.breakfast} />
              <Row label="Spuntino mattina" value={day.home_meals.snack_morning} />
              <Section label="Pranzo" value={day.home_meals.lunch} />
              <Row label="Spuntino pomeriggio" value={day.home_meals.snack_afternoon} />
              <Section label="Cena" value={day.home_meals.dinner} />
              <Row label="Spuntino sera" value={day.home_meals.snack_evening} />
            </div>
            <div>
              <ColumnHeader label="Scuola" icon={GraduationCap} category="scuola" />
              <Section label="Pranzo" value={day.school_meal} />
              <Row label="Merenda mattina" value={day.snack_morning} />
              <Row label="Merenda pomeriggio" value={day.snack_afternoon} />
            </div>
          </div>
        </Card>
      ))}
    </>
  )
}
