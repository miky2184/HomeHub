import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AppLayout } from './layout/AppLayout'
import { CalendarPage } from './pages/CalendarPage'
import { ChoresPage } from './pages/ChoresPage'
import { HomePage } from './pages/HomePage'
import { InventoryPage } from './pages/InventoryPage'
import { MenuPage } from './pages/MenuPage'
import { SettingsPage } from './pages/SettingsPage'
import { ShoppingPage } from './pages/ShoppingPage'
import { TodoPage } from './pages/TodoPage'
import { TrainingPage } from './pages/TrainingPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<HomePage />} />
            <Route path="calendario" element={<CalendarPage />} />
            <Route path="todo" element={<TodoPage />} />
            <Route path="manutenzione" element={<ChoresPage />} />
            <Route path="menu" element={<MenuPage />} />
            <Route path="allenamenti" element={<TrainingPage />} />
            <Route path="spesa" element={<ShoppingPage />} />
            <Route path="inventory" element={<InventoryPage />} />
            <Route path="impostazioni" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
