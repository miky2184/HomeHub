import { useTrainingActivityDetail } from '../api/hooks'
import { Modal } from './Modal'

interface ActivityDetailModalProps {
  date: string
  title: string
  onClose: () => void
}

function formatPace(passoSec: number | null): string | null {
  if (!passoSec) return null
  const min = Math.floor(passoSec / 60)
  const sec = Math.round(passoSec % 60)
  return `${min}:${String(sec).padStart(2, '0')} /km`
}

function Stat({ label, value }: { label: string; value: string | null }) {
  if (!value) return null
  return (
    <div>
      <p style={{ margin: 0, fontSize: 'var(--fs-label)', color: 'var(--text-muted)' }}>{label}</p>
      <p style={{ margin: '2px 0 0', fontSize: 'var(--fs-body)', fontWeight: 600 }}>{value}</p>
    </div>
  )
}

export function ActivityDetailModal({ date, title, onClose }: ActivityDetailModalProps) {
  const { data, isLoading, isError } = useTrainingActivityDetail(date)

  return (
    <Modal title={title} onClose={onClose}>
      {isLoading && <p style={{ color: 'var(--text-secondary)' }}>Caricamento…</p>}
      {isError && <p style={{ color: 'var(--danger)' }}>Impossibile caricare il dettaglio.</p>}
      {data && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <Stat label="Distanza" value={data.distanza_m ? `${(data.distanza_m / 1000).toFixed(1)} km` : null} />
          <Stat label="Durata" value={data.durata_sec ? `${Math.round(data.durata_sec / 60)} min` : null} />
          <Stat label="Passo medio" value={formatPace(data.passo_sec)} />
          <Stat label="Cadenza" value={data.cadenza ? `${data.cadenza} spm` : null} />
          <Stat label="FC media" value={data.fc_media ? `${data.fc_media} bpm` : null} />
          <Stat label="FC massima" value={data.fc_max ? `${data.fc_max} bpm` : null} />
          <Stat label="Dislivello" value={data.ascesa_m ? `${data.ascesa_m} m` : null} />
          <Stat label="Calorie" value={data.calorie ? `${data.calorie} kcal` : null} />
          <Stat label="Effetto aerobico" value={data.te_aerobico ? data.te_aerobico.toFixed(1) : null} />
          <Stat label="TSS" value={data.tss ? data.tss.toFixed(0) : null} />
          <Stat label="SWOLF" value={data.swolf ? data.swolf.toFixed(0) : null} />
        </div>
      )}
    </Modal>
  )
}
