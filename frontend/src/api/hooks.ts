import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './client'
import type {
  CalendarEvent,
  HomeSummary,
  InventoryAlert,
  MenuWeek,
  ShoppingItem,
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

// --- Menu ---

export function useMenuWeek(weekStartDate: string) {
  return useQuery({
    queryKey: ['menu-week', weekStartDate],
    queryFn: () => api.get<MenuWeek>(`/api/menu/week?week_start_date=${weekStartDate}`),
  })
}

export function useUpsertSchoolMenu(weekStartDate: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { day_of_week: number; meal_text: string }) =>
      api.put('/api/menu/school', { week_start_date: weekStartDate, ...payload }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu-week', weekStartDate] })
      queryClient.invalidateQueries({ queryKey: ['home-summary'] })
    },
  })
}

// --- Allenamenti ---

export function useTrainingWeek(weekStartDate: string) {
  return useQuery({
    queryKey: ['training-week', weekStartDate],
    queryFn: () => api.get<TrainingSession[]>(`/api/training/week?week_start_date=${weekStartDate}`),
  })
}

export function useUpsertTrainingSession(weekStartDate: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { day_of_week: number; session_text: string }) =>
      api.put('/api/training', { week_start_date: weekStartDate, ...payload }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['training-week', weekStartDate] })
      queryClient.invalidateQueries({ queryKey: ['home-summary'] })
    },
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

// --- Home inventory ---

export function useInventoryAlerts() {
  return useQuery({
    queryKey: ['inventory-alerts'],
    queryFn: () => api.get<InventoryAlert[]>('/api/inventory/alerts'),
    refetchInterval: 15 * 60_000,
  })
}

export function useMarkConsumed() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (itemId: string) => api.patch<InventoryAlert[]>(`/api/inventory/${itemId}/consume`),
    onSuccess: (alerts) => {
      queryClient.setQueryData(['inventory-alerts'], alerts)
      queryClient.invalidateQueries({ queryKey: ['home-summary'] })
    },
  })
}
