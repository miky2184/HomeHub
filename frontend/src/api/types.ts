// Rispecchia lo schema unificato "HomeHub" esposto dal backend
// (backend/app/schemas/common.py) — un solo posto da tenere allineato.

export interface CalendarEvent {
  id: string
  calendar_id: string
  calendar_label: string
  title: string
  start: string
  end: string
  all_day: boolean
}

export interface CalendarInfo {
  id: string
  label: string
}

export interface HomeMeals {
  breakfast: string | null
  snack_morning: string | null
  lunch: string | null
  snack_afternoon: string | null
  dinner: string | null
  snack_evening: string | null
}

export interface MenuDay {
  date: string
  day_of_week: number
  school_meal: string | null
  home_meals: HomeMeals
  snack_morning: string | null
  snack_afternoon: string | null
}

export interface MenuWeek {
  week_start_date: string
  days: MenuDay[]
}

export interface SchoolMenuTemplateEntry {
  cycle_week: number
  day_of_week: number
  meal_text: string
}

export interface SchoolMenuCycleAnchor {
  anchor_monday: string
  anchor_cycle_week: number
}

export interface SnackTemplateEntry {
  day_of_week: number
  snack_type: 'mattina' | 'pomeriggio'
  snack_text: string
}

export interface MenuSettings {
  school_template: SchoolMenuTemplateEntry[]
  cycle_anchor: SchoolMenuCycleAnchor | null
  snacks: SnackTemplateEntry[]
}

export interface TrainingSession {
  id: number
  week_start_date: string
  day_of_week: number
  session_text: string
  done: boolean
  garmin_note: string | null
  sport_type: string | null
}

export interface TrainingActivityDetail {
  data: string
  tipo: string | null
  titolo: string | null
  distanza_m: number | null
  durata_sec: number | null
  calorie: number | null
  fc_media: number | null
  fc_max: number | null
  te_aerobico: number | null
  passo_sec: number | null
  cadenza: number | null
  tss: number | null
  ascesa_m: number | null
  swolf: number | null
}

export interface ShoppingItem {
  id: string
  name: string
  checked: boolean
  specification: string | null
}

export interface InventoryAlert {
  id: number
  item_name: string
  quantity: number | null
  unit: string | null
  expiry_date: string | null
  days_to_expiry: number | null
  container_name: string | null
  reason: 'expired' | 'critical' | 'warning'
}

// "Sfoglia per contenitore": tutto il contenuto di home_inventory, non solo
// ciò che scade a breve (vedi InventoryAlert sopra) — sostituisce il foglio
// di carta sul frigo per sapere cosa c'è in un cassetto del freezer.
export interface InventoryItem {
  id: number
  name: string
  quantity: number | null
  unit: string | null
  expiry_date: string | null
  category: string | null
}

export interface InventoryContainer {
  id: number
  name: string
  items: InventoryItem[]
}

export interface HourlyForecast {
  time: string
  temperature_c: number | null
  condition: string | null
  precipitation_probability: number | null
}

export interface DailyForecast {
  date: string
  condition: string | null
  temperature_min: number | null
  temperature_max: number | null
  precipitation_probability_max: number | null
}

export interface WeatherSnapshot {
  temperature_c: number | null
  condition: string | null
  city: string | null
  hourly: HourlyForecast[]
  daily: DailyForecast[]
  precipitation_alert: string | null
}

export type TodoPriority = 'alta' | 'media' | 'bassa'

export interface TodoItem {
  id: number
  title: string
  assignee: string | null
  priority: TodoPriority
  due_date: string | null
  done: boolean
  created_at: string
}

export interface TodoItemInput {
  title: string
  assignee: string | null
  priority: TodoPriority
  due_date: string | null
}

export interface TodoSummary {
  pending_count: number
  top: TodoItem[]
}

// Manutenzione: attività di casa ricorrenti per intervallo, non una-tantum
// come i Todo (vedi backend/app/db/models.py:Chore). next_due_date è
// calcolato dal backend, non un campo salvato.
export interface Chore {
  id: number
  title: string
  interval_days: number
  last_done_date: string | null
  next_due_date: string
  assignee: string | null
  notes: string | null
  created_at: string
}

export interface ChoreInput {
  title: string
  interval_days: number
  last_done_date: string | null
  assignee: string | null
  notes: string | null
}

export interface ChoreSummary {
  due_count: number
  top: Chore[]
}

// Spedizioni: tracking manuale (numero + corriere), stato letto on-demand
// dal corriere quando il tab/la card Home vengono aperti (vedi
// backend/app/services/aggregator.refresh_stale_shipments). Solo
// carrier="poste_italiane" ha tracking automatico oggi.
export type ShipmentCarrier = 'poste_italiane' | 'altro'

export interface ShipmentEvent {
  at: string
  description: string
  location: string | null
}

export interface Shipment {
  id: number
  tracking_number: string
  carrier: ShipmentCarrier
  label: string | null
  status: string | null
  delivered: boolean
  last_event_at: string | null
  last_event_description: string | null
  last_event_location: string | null
  events: ShipmentEvent[]
  last_polled_at: string | null
  last_poll_error: string | null
  created_at: string
}

export interface ShipmentInput {
  tracking_number: string
  carrier: ShipmentCarrier
  label: string | null
}

export interface ShipmentSummary {
  in_transit_count: number
  top: Shipment[]
}

export interface HomeSummary {
  now: string
  family_name: string
  weather: WeatherSnapshot | null
  saint_of_day: string | null
  quote_of_day: string | null
  today_events: CalendarEvent[]
  today_menu: MenuDay | null
  next_training: TrainingSession | null
  shopping_preview: ShoppingItem[]
  shopping_total_count: number
  inventory_alerts: InventoryAlert[]
  chores: ChoreSummary
  todos: TodoSummary
  shipments: ShipmentSummary
}

// Impostazioni: config effettiva (.env + override salvati da qui, vedi
// backend/app/core/runtime_settings.py). I campi segreto non tornano mai
// col valore vero, solo "<campo>_set" per sapere se sono sovrascritti.
export interface AppSettings {
  family_name: string
  weather_city: string
  weather_latitude: number | null
  weather_longitude: number | null
  background_theme: string
  shopping_preview_limit: number
  google_client_id: string
  google_client_secret_set: boolean
  google_refresh_token_set: boolean
  google_calendar_ids: string[]
  bring_email: string
  bring_password_set: boolean
  garmin_email: string
  garmin_password_set: boolean
}

// PATCH parziale: solo i campi presenti vengono toccati. "" o null = rimuove
// l'override e torna a .env; per i campi segreto, ometterli = non toccare.
export interface AppSettingsUpdate {
  family_name?: string
  weather_city?: string
  weather_latitude?: number | null
  weather_longitude?: number | null
  background_theme?: string
  shopping_preview_limit?: number | null
  google_client_id?: string
  google_client_secret?: string
  google_refresh_token?: string
  google_calendar_ids?: string[] | null
  bring_email?: string
  bring_password?: string
  garmin_email?: string
  garmin_password?: string
}

// Login unico e condiviso (vedi backend/app/core/auth.py). auth_required
// false = password non ancora configurata in backend/.env: l'app funziona
// senza mai chiedere login (vedi anche useAuthStatus in hooks.ts).
export interface AuthStatus {
  auth_required: boolean
  authenticated: boolean
}
