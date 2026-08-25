import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './client'
import type {
  AppSettings,
  AppSettingsUpdate,
  CalendarEvent,
  CalendarInfo,
  Chore,
  ChoreInput,
  HomeSummary,
  InventoryAlert,
  InventoryContainer,
  InventoryItem,
  MenuSettings,
  MenuWeek,
  SchoolMenuCycleAnchor,
  SchoolMenuTemplateEntry,
  ShoppingItem,
  SnackTemplateEntry,
  TodoItem,
  TodoItemInput,
  TrainingActivityDetail,
  TrainingSession,
} from './types'

// --- Home ---

export function useHomeSummary() {
  return useQuery({
    queryKey: ['home-summary'],
    queryFn: () => api.get<HomeSummary>('/api/home/summary'),
    refetchInterval: 60_000,
  })
}

// --- Calendario ---

export function useCalendarEvents() {
  return useQuery({
    queryKey: ['calendar-events'],
    queryFn: () => api.get<CalendarEvent[]>('/api/calendar/events'),
    refetchInterval: 5 * 60_000,
  })
}

export function useCalendars() {
  return useQuery({
    queryKey: ['calendars'],
    queryFn: () => api.get<CalendarInfo[]>('/api/calendar/calendars'),
    staleTime: 60 * 60_000, // cambiano raramente, niente bisogno di rifetch frequenti
  })
}

export function useAddCalendarEvent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { calendar_id: string; title: string; start: string; end: string; all_day?: boolean }) =>
      api.post<CalendarEvent>('/api/calendar/events', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] })
      queryClient.invalidateQueries({ queryKey: ['home-summary'] })
    },
  })
}

export function useUpdateCalendarEvent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      ...payload
    }: {
      id: string
      calendar_id: string
      title: string
      start: string
      end: string
      all_day?: boolean
    }) => api.patch<CalendarEvent>(`/api/calendar/events/${id}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] })
      queryClient.invalidateQueries({ queryKey: ['home-summary'] })
    },
  })
}

export function useDeleteCalendarEvent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, calendarId }: { id: string; calendarId: string }) =>
      api.delete<void>(`/api/calendar/events/${id}?calendar_id=${encodeURIComponent(calendarId)}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-events'] })
      queryClient.invalidateQueries({ queryKey: ['home-summary'] })
    },
  })
}

// --- Menu ---

export function useMenuWeek(weekStartDate: string) {
  return useQuery({
    queryKey: ['menu-week', weekStartDate],
    queryFn: () => api.get<MenuWeek>(`/api/menu/week?week_start_date=${weekStartDate}`),
  })
}

export function useMenuSettings() {
  return useQuery({
    queryKey: ['menu-settings'],
    queryFn: () => api.get<MenuSettings>('/api/menu/settings'),
  })
}

function useInvalidateMenu() {
  const queryClient = useQueryClient()
  return () => {
    queryClient.invalidateQueries({ queryKey: ['menu-week'] })
    queryClient.invalidateQueries({ queryKey: ['menu-settings'] })
    queryClient.invalidateQueries({ queryKey: ['home-summary'] })
  }
}

export function useUpsertSchoolTemplate() {
  const invalidate = useInvalidateMenu()
  return useMutation({
    mutationFn: (entries: SchoolMenuTemplateEntry[]) =>
      api.put('/api/menu/settings/school-template', { entries }),
    onSuccess: invalidate,
  })
}

export function useUpsertSchoolAnchor() {
  const invalidate = useInvalidateMenu()
  return useMutation({
    mutationFn: (payload: SchoolMenuCycleAnchor) => api.put('/api/menu/settings/school-anchor', payload),
    onSuccess: invalidate,
  })
}

export function useUpsertSnacks() {
  const invalidate = useInvalidateMenu()
  return useMutation({
    mutationFn: (entries: SnackTemplateEntry[]) => api.put('/api/menu/settings/snacks', { entries }),
    onSuccess: invalidate,
  })
}

// --- Allenamenti ---

export function useTrainingWeek(weekStartDate: string) {
  return useQuery({
    queryKey: ['training-week', weekStartDate],
    queryFn: () => api.get<TrainingSession[]>(`/api/training/week?week_start_date=${weekStartDate}`),
    // Il piano ora arriva da Garmin/dieta.allenamento (non più editabile a
    // mano dalla UI): forza un fetch fresco ogni volta che si torna sulla
    // tab Attività, invece di fidarsi della cache di TanStack Query.
    refetchOnMount: 'always',
  })
}

export function useTrainingActivityDetail(activityDate: string | null) {
  return useQuery({
    queryKey: ['training-activity', activityDate],
    queryFn: () => api.get<TrainingActivityDetail>(`/api/training/activity/${activityDate}`),
    enabled: activityDate !== null,
  })
}

export function useMarkTrainingDone(weekStartDate: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, done }: { id: number; done: boolean }) =>
      api.patch(`/api/training/${id}/done?done=${done}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['training-week', weekStartDate] })
      queryClient.invalidateQueries({ queryKey: ['home-summary'] })
    },
  })
}

// --- Spesa (Bring!) ---

export function useShoppingList() {
  return useQuery({
    queryKey: ['shopping-list'],
    queryFn: () => api.get<ShoppingItem[]>('/api/shopping'),
    refetchInterval: 2 * 60_000,
  })
}

export function useAddShoppingItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { name: string; specification?: string }) =>
      api.post<ShoppingItem[]>('/api/shopping', payload),
    onSuccess: (items) => {
      queryClient.setQueryData(['shopping-list'], items)
      queryClient.invalidateQueries({ queryKey: ['home-summary'] })
    },
  })
}

export function useToggleShoppingItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (itemId: string) => api.patch<ShoppingItem[]>(`/api/shopping/${itemId}/toggle`),
    onSuccess: (items) => {
      queryClient.setQueryData(['shopping-list'], items)
      queryClient.invalidateQueries({ queryKey: ['home-summary'] })
    },
  })
}

export function useRemoveShoppingItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (itemId: string) => api.delete<ShoppingItem[]>(`/api/shopping/${itemId}`),
    onSuccess: (items) => {
      queryClient.setQueryData(['shopping-list'], items)
      queryClient.invalidateQueries({ queryKey: ['home-summary'] })
    },
  })
}

// --- Home inventory (per lo più sola lettura: creare/eliminare oggetti resta
// nella web app dedicata; l'unica scrittura da qui è l'aggiustamento rapido
// della quantità, vedi useAdjustItemQuantity) ---

export function useInventoryAlerts() {
  return useQuery({
    queryKey: ['inventory-alerts'],
    queryFn: () => api.get<InventoryAlert[]>('/api/inventory/alerts'),
    refetchInterval: 15 * 60_000,
  })
}

export function useInventoryContainers() {
  return useQuery({
    queryKey: ['inventory-containers'],
    queryFn: () => api.get<InventoryContainer[]>('/api/inventory/containers'),
    refetchInterval: 15 * 60_000,
  })
}

export function useAdjustItemQuantity() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ itemId, delta }: { itemId: number; delta: number }) =>
      api.patch<InventoryItem>(`/api/inventory/items/${itemId}/quantity`, { delta }),
    onSuccess: () => {
      // Niente aggiornamento ottimistico: la quantità aggiornata compare sia
      // nel browse per contenitore sia (se in scadenza) negli alert di Home.
      queryClient.invalidateQueries({ queryKey: ['inventory-containers'] })
      queryClient.invalidateQueries({ queryKey: ['inventory-alerts'] })
      queryClient.invalidateQueries({ queryKey: ['home-summary'] })
    },
  })
}

// --- Todo ---

export function useTodos(includeDone = true) {
  return useQuery({
    queryKey: ['todos', includeDone],
    queryFn: () => api.get<TodoItem[]>(`/api/todos?include_done=${includeDone}`),
  })
}

function useInvalidateTodos() {
  const queryClient = useQueryClient()
  return () => {
    queryClient.invalidateQueries({ queryKey: ['todos'] })
    queryClient.invalidateQueries({ queryKey: ['home-summary'] })
  }
}

export function useCreateTodo() {
  const invalidate = useInvalidateTodos()
  return useMutation({
    mutationFn: (payload: TodoItemInput) => api.post<TodoItem>('/api/todos', payload),
    onSuccess: invalidate,
  })
}

export function useUpdateTodo() {
  const invalidate = useInvalidateTodos()
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: number } & Partial<TodoItemInput & { done: boolean }>) =>
      api.patch<TodoItem>(`/api/todos/${id}`, payload),
    onSuccess: invalidate,
  })
}

export function useDeleteTodo() {
  const invalidate = useInvalidateTodos()
  return useMutation({
    mutationFn: (id: number) => api.delete<void>(`/api/todos/${id}`),
    onSuccess: invalidate,
  })
}

// --- Manutenzione (attività di casa ricorrenti per intervallo, non
// una-tantum come i Todo) ---

export function useChores() {
  return useQuery({
    queryKey: ['chores'],
    queryFn: () => api.get<Chore[]>('/api/chores'),
  })
}

function useInvalidateChores() {
  const queryClient = useQueryClient()
  return () => {
    queryClient.invalidateQueries({ queryKey: ['chores'] })
    queryClient.invalidateQueries({ queryKey: ['home-summary'] })
  }
}

export function useCreateChore() {
  const invalidate = useInvalidateChores()
  return useMutation({
    mutationFn: (payload: ChoreInput) => api.post<Chore>('/api/chores', payload),
    onSuccess: invalidate,
  })
}

export function useUpdateChore() {
  const invalidate = useInvalidateChores()
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: number } & Partial<ChoreInput>) =>
      api.patch<Chore>(`/api/chores/${id}`, payload),
    onSuccess: invalidate,
  })
}

export function useDeleteChore() {
  const invalidate = useInvalidateChores()
  return useMutation({
    mutationFn: (id: number) => api.delete<void>(`/api/chores/${id}`),
    onSuccess: invalidate,
  })
}

// --- Impostazioni (nome famiglia, meteo, palette, credenziali integrazioni:
// se salvate qui vincono su .env, vedi backend/app/core/runtime_settings.py) ---

export function useAppSettings() {
  return useQuery({
    queryKey: ['app-settings'],
    queryFn: () => api.get<AppSettings>('/api/settings'),
    staleTime: 60_000,
  })
}

export function useUpdateAppSettings() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: AppSettingsUpdate) => api.put<AppSettings>('/api/settings', payload),
    onSuccess: (data) => {
      queryClient.setQueryData(['app-settings'], data)
      // Nome famiglia e meteo compaiono anche in Home.
      queryClient.invalidateQueries({ queryKey: ['home-summary'] })
    },
  })
}

