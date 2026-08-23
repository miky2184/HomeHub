import type { ReactNode } from 'react'

interface CardProps {
  label: string
  variant?: 'default' | 'warning'
  onClick?: () => void
  children: ReactNode
}

export function Card({ label, variant = 'default', onClick, children }: CardProps) {
  const Tag = onClick ? 'button' : 'div'
  return (
    <Tag
      onClick={onClick}
      style={{
        display: 'block',
        width: '100%',
        textAlign: 'left',
        background: variant === 'warning' ? 'var(--bg-warning)' : 'var(--bg-card)',
        border: 'none',
        borderRadius: 'var(--radius-card)',
        padding: '16px 20px',
        cursor: onClick ? 'pointer' : 'default',
        color: 'inherit',
        font: 'inherit',
      }}
    >
      <p
        style={{
          margin: '0 0 8px',
          fontSize: 'var(--fs-label)',
          color: variant === 'warning' ? 'var(--warning)' : 'var(--text-muted)',
        }}
      >
        {label}
      </p>
      {children}
    </Tag>
  )
}
