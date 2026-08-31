import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useShipmentRoute } from '../api/hooks'
import { formatEventDateTime } from '../lib/shipments'

/** Mappa del percorso indicativo di una spedizione: Poste non fornisce
 * indirizzi di mittente/destinatario nel tracciamento pubblico (solo nomi
 * di città/centro di smistamento per tappa — vedi backend/app/adapters/
 * geocoding.py), quindi qui i marker sono a livello di città/hub, non
 * porta a porta. Leaflet "vanilla" (non react-leaflet, non una dipendenza
 * del progetto) con cerchi colorati invece dei pin di default: evita il
 * classico problema di bundling di Leaflet con Vite/webpack (i path delle
 * icone di default non si risolvono senza configurazione ad hoc). */
export function ShipmentRouteMap({ shipmentId }: { shipmentId: number }) {
  const { data: route, isLoading } = useShipmentRoute(shipmentId)
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)

  useEffect(() => {
    if (!containerRef.current || !route || route.length === 0) return

    const map = L.map(containerRef.current, { zoomControl: false, attributionControl: true })
    mapRef.current = map
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18,
    }).addTo(map)

    // Colori hardcoded (non var(--cat-spedizioni-fg)): Leaflet li applica come
    // attributi SVG via JS, non tramite un foglio di stile, quindi una CSS
    // custom property qui non verrebbe risolta dal browser — stesso valore
    // di --cat-spedizioni-fg in styles/theme.css, tenerli allineati a mano.
    const ROUTE_COLOR = '#bd5c5c'
    const ROUTE_COLOR_LIGHT = '#e0a3a3'

    const latLngs = route.map((p) => L.latLng(p.lat, p.lon))
    route.forEach((point, i) => {
      const isLast = i === route.length - 1
      L.circleMarker(L.latLng(point.lat, point.lon), {
        radius: isLast ? 9 : 6,
        color: ROUTE_COLOR,
        fillColor: isLast ? ROUTE_COLOR : ROUTE_COLOR_LIGHT,
        fillOpacity: 1,
        weight: 2,
      })
        .bindPopup(`<strong>${point.place}</strong><br />${formatEventDateTime(point.at)}`)
        .addTo(map)
    })
    if (latLngs.length > 1) {
      L.polyline(latLngs, { color: ROUTE_COLOR, weight: 3, opacity: 0.7, dashArray: '6 6' }).addTo(map)
    }
    map.fitBounds(L.latLngBounds(latLngs), { padding: [24, 24], maxZoom: 10 })

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [route])

  if (isLoading) {
    return <p style={{ margin: '12px 0 0', color: 'var(--text-secondary)', fontSize: 'var(--fs-label)' }}>Carico la mappa…</p>
  }
  if (!route || route.length === 0) {
    return null // Nessuna tappa geolocalizzabile: niente mappa, l'elenco testuale sotto basta
  }
  return (
    <div
      ref={containerRef}
      style={{ height: 220, borderRadius: 'var(--radius-control)', overflow: 'hidden', margin: '12px 0' }}
    />
  )
}
