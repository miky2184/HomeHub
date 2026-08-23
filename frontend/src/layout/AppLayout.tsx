import { Outlet } from 'react-router-dom'
import { Rail } from '../components/Rail'
import { useIdleRedirect } from '../hooks/useIdleRedirect'

export function AppLayout() {
  useIdleRedirect()

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Rail />
      <main
        style={{
          flex: 1,
          minWidth: 0,
          overflowY: 'auto',
          padding: '20px 20px 40px',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--gap-md)',
        }}
      >
        <Outlet />
      </main>
    </div>
  )
}
