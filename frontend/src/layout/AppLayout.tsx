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
        }}
      >
        {/* HomeHub è pensato per il monitor verticale del NUC (~950px di
            contenuto): senza questo limite, su un browser desktop largo
            (es. mentre si sviluppa/testa da remoto) card e calendario si
            allargano a dismisura invece di restare compatti. */}
        <div
          style={{
            maxWidth: 960,
            margin: '0 auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--gap-md)',
          }}
        >
          <Outlet />
        </div>
      </main>
    </div>
  )
}
