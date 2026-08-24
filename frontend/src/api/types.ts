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

export interface MenuDay {
  date: string
  day_of_week: number
  school_meal: string | null
  home_meal: string | null
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

export interface HourlyForecast {
  time: string
  temperature_c: number | null
  condition: string | null
  precipitation_probability: number | null
}

export interface WeatherSnapshot {
  temperature_c: number | null
  condition: string | null
  city: string | null
  hourly: HourlyForecast[]
  precipitation_alert: string | null
}

export interface HomeSummary {
  now: string
  weather: WeatherSnapshot | null
  saint_of_day: string | null
  quote_of_day: string | null
  today_events: CalendarEvent[]
  today_menu: MenuDay | null
  next_training: TrainingSession | null
  shopping_preview: ShoppingItem[]
  shopping_total_count: number
  inventory_alerts: InventoryAlert[]
}
