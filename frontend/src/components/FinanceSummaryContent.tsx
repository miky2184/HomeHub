import type { FinanceSummary } from '../api/types'
import { ALERT_COLOR } from '../lib/finance'

interface FinanceSummaryContentProps {
  finance: FinanceSummary
  maxCategories?: number
  maxUpcoming?: number
}

/** Contenuto condiviso tra la card Home (compatta) e il tab Finanze
 * completo. ⚠️ Non aggiungere MAI qui la visualizzazione di un importo:
 * FinanceSummary non ne contiene nemmeno uno per design (vedi
 * backend/app/adapters/finance.py) — solo percentuali/stati. */
export function FinanceSummaryContent({ finance, maxCategories, maxUpcoming }: FinanceSummaryContentProps) {
  const categories = maxCategories ? finance.categories.slice(0, maxCategories) : finance.categories
  const upcoming = maxUpcoming ? finance.upcoming_expenses.slice(0, maxUpcoming) : finance.upcoming_expenses

  return (
    <>
      {categories.length === 0 ? (
        <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-secondary)' }}>
          Nessun budget definito per questo mese
        </p>
      ) : (
        categories.map((cat) => (
          <div key={cat.label} style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
              <span style={{ fontSize: 'var(--fs-body)', fontWeight: 600, color: 'var(--text-primary)' }}>
                {cat.label}
              </span>
              <span style={{ fontSize: 'var(--fs-label)', fontWeight: 700, color: ALERT_COLOR[cat.alert_level] }}>
                {Math.round(cat.perc_proiezione)}% proiezione
              </span>
            </div>
            <div style={{ height: 8, borderRadius: 4, background: 'var(--border)', overflow: 'hidden' }}>
              <div
                style={{
                  height: '100%',
                  width: `${Math.min(cat.perc_proiezione, 100)}%`,
                  background: ALERT_COLOR[cat.alert_level],
                  borderRadius: 4,
                }}
              />
            </div>
            <p style={{ margin: '4px 0 0', fontSize: 11, color: 'var(--text-muted)' }}>
              Speso finora: {Math.round(cat.perc_speso)}% del budget
            </p>
          </div>
        ))
      )}

      {upcoming.length > 0 && (
        <div style={{ marginTop: 8, paddingTop: 10, borderTop: '1px solid var(--border)' }}>
          <p style={{ margin: '0 0 6px', fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>
            Prossime scadenze
          </p>
          {upcoming.map((exp, i) => (
            <div
              key={i}
              style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 'var(--fs-label)' }}
            >
              <span style={{ color: 'var(--text-primary)' }}>{exp.beneficiario ?? 'Movimento pianificato'}</span>
              <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{exp.period}</span>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
