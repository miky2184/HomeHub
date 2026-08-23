import { Card } from '../components/Card'

/** Tab opzionale — in attesa di decidere cosa esporre dalla web app finanze
 * esistente (vedi ARCHITECTURE.md §5 e backend/app/adapters/finance_app.py). */
export function FinancePage() {
  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-heading)', margin: '4px 0 8px' }}>Finanze</h1>
      <Card label="In arrivo">
        <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-secondary)' }}>
          Questa sezione è opzionale: da definire cosa mostrare dalla web app finanze esistente.
        </p>
      </Card>
    </>
  )
}
