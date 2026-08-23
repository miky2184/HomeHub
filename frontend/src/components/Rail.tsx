import { NavLink } from 'react-router-dom'
import { Calendar, Home, House, Settings, ShoppingCart, SoupIcon, Wallet, Dumbbell } from 'lucide-react'
import type { ComponentType } from 'react'
import { CATEGORY_COLORS, type Category } from '../styles/categories'

interface Tab {
  to: string
  label: string
  Icon: ComponentType<{ size?: number }>
  category: Category
}

const TABS: Tab[] = [
  { to: '/', label: 'Home', Icon: Home, category: 'home' },
  { to: '/calendario', label: 'Agenda', Icon: Calendar, category: 'agenda' },
  { to: '/menu', label: 'Cucina', Icon: SoupIcon, category: 'cucina' },
  { to: '/allenamenti', label: 'Attività', Icon: Dumbbell, category: 'attivita' },
  { to: '/spesa', label: 'Spesa', Icon: ShoppingCart, category: 'spesa' },
  { to: '/inventory', label: 'Casa', Icon: House, category: 'casa' },
  { to: '/finanze', label: 'Finanze', Icon: Wallet, category: 'finanze' },
  { to: '/impostazioni', label: 'Impostazioni', Icon: Settings, category: 'home' },
]

export function Rail() {
  return (
    <nav
      aria-label="Sezioni HomeHub"
      style={{
        width: 128,
        flexShrink: 0,
        background: 'var(--bg-rail)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'stretch',
        gap: 10,
        padding: '20px 14px',
        overflowY: 'auto',
      }}
    >
      <img
        src="/logo-mark.png"
        alt="HomeHub"
        style={{ width: 48, height: 48, borderRadius: 16, margin: '0 auto 10px' }}
      />
      {TABS.map(({ to, label, Icon, category }) => {
        const colors = CATEGORY_COLORS[category]
        return (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 6,
              padding: '10px 4px',
              borderRadius: 'var(--radius-control)',
              color: isActive ? colors.fg : 'var(--text-secondary)',
              background: isActive ? colors.bg : 'transparent',
              textDecoration: 'none',
            })}
          >
            <Icon size={22} />
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: 0.3,
                textTransform: 'uppercase',
                textAlign: 'center',
              }}
            >
              {label}
            </span>
          </NavLink>
        )
      })}
    </nav>
  )
}
