import { Settings } from 'lucide-react'
import { Card } from '../components/Card'

/** Stub — impostazioni previste in futuro: nome membro famiglia, città meteo,
 * subnet LAN per il bypass Basic Auth, credenziali integrazioni, ecc. */
export function SettingsPage() {
  return (
    <>
      <h1 style={{ fontSize: 'var(--fs-greeting)', margin: '4px 0 8px' }}>Impostazioni</h1>
      <Card label="In arrivo" icon={Settings} category="home">
        <p style={{ margin: 0, fontSize: 'var(--fs-body)', color: 'var(--text-secondary)' }}>
          Qui arriveranno le impostazioni (nome di famiglia, città meteo, integrazioni).
        </p>
      </Card>
    </>
  )
}
