import type { CSSProperties } from 'react'

export const inputStyle: CSSProperties = {
  flex: 1,
  minWidth: 160,
  padding: '10px 12px',
  borderRadius: 'var(--radius-control)',
  border: '1px solid var(--border-strong)',
  background: 'var(--bg-input)',
  color: 'var(--text-primary)',
  fontSize: 'var(--fs-label)',
}

export const buttonStyle: CSSProperties = {
  padding: '10px 18px',
  borderRadius: 'var(--radius-control)',
  border: 'none',
  background: 'var(--accent)',
  color: 'var(--on-accent)',
  fontSize: 'var(--fs-label)',
  fontWeight: 700,
  cursor: 'pointer',
}

export const ghostButtonStyle: CSSProperties = {
  padding: '8px 14px',
  borderRadius: 'var(--radius-control)',
  border: '1px solid var(--border-strong)',
  background: 'var(--bg-input)',
  color: 'var(--text-secondary)',
  fontSize: 'var(--fs-label)',
  cursor: 'pointer',
}
