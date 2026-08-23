import type { ComponentType, ReactNode } from 'react'
import { ArrowRight } from 'lucide-react'
import { CATEGORY_COLORS, type Category } from '../styles/categories'

interface CardProps {
  label: string
  icon?: ComponentType<{ size?: number }>
  category?: Category
  variant?: 'default' | 'warning'
  footerLabel?: string
  onFooterClick?: () => void
  children: ReactNode
}

export function Card({ label, icon: Icon, category = 'home', variant = 'default', footerLabel, onFooterClick, children }: CardProps) {
  const colors = CATEGORY_COLORS[category]

  return (
    <div
      style={{
        background: variant === 'warning' ? '#fbe9df' : 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-card)',
        padding: '18px 20px',
        boxShadow: '0 2px 10px rgba(46, 43, 38, 0.04)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
        {Icon && (
          <span
            aria-hidden
            style={{
              width: 34,
              height: 34,
              borderRadius: '50%',
              background: variant === 'warning' ? '#f3d3bf' : colors.bg,
              color: variant === 'warning' ? 'var(--warning)' : colors.fg,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <Icon size={18} />
          </span>
        )}
        <p
          style={{
            margin: 0,
            fontFamily: 'var(--font-heading)',
            fontWeight: 600,
            fontSize: 'var(--fs-heading)',
            letterSpacing: 0.2,
            color: 'var(--text-primary)',
          }}
        >
          {label}
        </p>
      </div>

      {children}

      {footerLabel && (
        <button
          onClick={onFooterClick}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            marginTop: 14,
            background: 'transparent',
            border: 'none',
            padding: 0,
            color: colors.fg,
            fontSize: 'var(--fs-label)',
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          {footerLabel} <ArrowRight size={15} />
        </button>
      )}
    </div>
  )
}
