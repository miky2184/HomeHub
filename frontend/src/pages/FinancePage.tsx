import { EyeOff, Wallet } from 'lucide-react'
import { useFinanceSummary, useGuestMode } from '../api/hooks'
import { Card } from '../components/Card'
import { FinanceSummaryContent } from '../components/FinanceSummaryContent'

export function FinancePage() {
  const { data: guestMode } = useGuestMode()
  const { data: finance, isLoading } = useFinanceSummary()

  if (guestMode?.enabled) {
    return (
      <>
        <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Finanze</h1>
        <Card label="Modalità ospiti attiva" icon={EyeOff} category="finanze">
          <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-secondary)' }}>
            Disattivala da Impostazioni (o dall'icona nel rail) per rivedere questa sezione.
          </p>
        </Card>
      </>
    )
  }

  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Finanze</h1>
      <p style={{ margin: '0 0 12px', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
        Solo percentuali di budget e promemoria scadenze — mai saldi o importi in euro, dato che questo schermo è
        visibile anche agli ospiti.
      </p>

      {isLoading && <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>}

      {!isLoading && !finance && (
        <Card label="Non configurato" icon={Wallet} category="finanze">
          <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-secondary)' }}>
            Integrazione finanze non ancora configurata (vedi backend/.env.example).
          </p>
        </Card>
      )}

      {finance && (
        <Card label="Andamento budget del mese" icon={Wallet} category="finanze">
          <FinanceSummaryContent finance={finance} maxUpcoming={5} />
        </Card>
      )}
    </>
  )
}
