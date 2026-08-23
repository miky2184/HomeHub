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

export interface MenuDay {
  day_of_week: number
  school_meal: string | null
  home_meal: string | null
}

export interface MenuWeek {
  week_start_date: string
  days: MenuDay[]
}

export interface TrainingSession {
  id: number
  week_start_date: string
  day_of_week: number
  session_text: string
  done: boolean
}

export interface ShoppingItem {
  id: string
  name: string
  checked: boolean
  specification: string | null
}

export interface InventoryAlert {
  id: string
  item_name: string
  quantity: number | null
  unit: string | null
  reason: string
}

export interface WeatherSnapshot {
  temperature_c: number | null
  condition: string | null
}

export interface HomeSummary {
  now: string
  weather: WeatherSnapshot | null
  today_events: CalendarEvent[]
  today_menu: MenuDay | null
  next_training: TrainingSession | null
  shopping_preview: ShoppingItem[]
  shopping_total_count: number
  inventory_alerts: InventoryAlert[]
}
