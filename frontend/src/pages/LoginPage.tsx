import { useState, type FormEvent } from 'react'
import { Home, Lock } from 'lucide-react'
import { useLogin } from '../api/hooks'
import { buttonStyle, inputStyle } from '../styles/controls'

/** Login unico e condiviso da tutta la famiglia (una password, non account
 * per persona — vedi backend/app/core/auth.py). Mostrata da App.tsx al
 * posto della dashboard finché non c'è un cookie di sessione valido; una
 * volta fatto login resta valido 30 giorni, quindi sul NUC in pratica non
 * si vede quasi mai. */
export function LoginPage({ onSuccess }: { onSuccess: () => void }) {
  const [password, setPassword] = useState('')
  const login = useLogin()

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!password) return
    login.mutate(password, { onSuccess })
  }

  return (
    <div
      style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-page)',
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          width: '100%',
          maxWidth: 340,
          padding: '32px 28px',
          borderRadius: 'var(--radius-card)',
          background: 'var(--bg-card)',
          boxShadow: '0 2px 10px rgba(46, 43, 38, 0.08)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 16,
        }}
      >
        <span
          style={{
            width: 56,
            height: 56,
            borderRadius: '50%',
            background: 'var(--cat-home-bg)',
            color: 'var(--cat-home-fg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Home size={28} />
        </span>
        <h1 style={{ margin: 0, fontSize: 'var(--fs-heading)', fontFamily: 'var(--font-heading)' }}>HomeHub</h1>

        <div style={{ width: '100%', position: 'relative' }}>
          <Lock
            size={16}
            style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }}
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            autoFocus
            style={{ ...inputStyle, width: '100%', paddingLeft: 36 }}
          />
        </div>

        {login.isError && (
          <p style={{ margin: 0, color: 'var(--danger)', fontSize: 'var(--fs-label)' }}>Password errata.</p>
        )}

        <button type="submit" disabled={login.isPending} style={{ ...buttonStyle, width: '100%' }}>
          Accedi
        </button>
      </form>
    </div>
  )
}
