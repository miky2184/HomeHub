import { NavLink } from 'react-router-dom'
import { Calendar, Dumbbell, Home, Package, ShoppingCart, UtensilsCrossed, Wallet } from 'lucide-react'
import type { ComponentType } from 'react'

interface Tab {
  to: string
  label: string
  Icon: ComponentType<{ size?: number }>
}

const TABS: Tab[] = [
  { to: '/', label: 'Home', Icon: Home },
  { to: '/calendario', label: 'Calendario', Icon: Calendar },
  { to: '/menu', label: 'Menu', Icon: UtensilsCrossed },
  { to: '/allenamenti', label: 'Allenamenti', Icon: Dumbbell },
  { to: '/spesa', label: 'Spesa', Icon: ShoppingCart },
  { to: '/inventory', label: 'Home inventory', Icon: Package },
  { to: '/finanze', label: 'Finanze', Icon: Wallet },
]

export function Rail() {
  return (
    <nav
      aria-label="Sezioni HomeHub"
      style={{
        width: 76,
        flexShrink: 0,
        background: 'var(--bg-rail)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 18,
        padding: '20px 0',
      }}
    >
      {TABS.map(({ to, label, Icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          aria-label={label}
          style={({ isActive }) => ({
            width: 52,
            height: 52,
            borderRadius: 'var(--radius-control)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: isActive ? 'var(--on-accent)' : 'var(--text-secondary)',
            background: isActive ? 'var(--accent)' : 'transparent',
            textDecoration: 'none',
          })}
        >
          <Icon size={26} />
        </NavLink>
      ))}
    </nav>
  )
}
