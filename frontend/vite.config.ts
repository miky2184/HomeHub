import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Stesso modello same-origin usato in produzione da nginx (vedi
    // frontend/nginx.conf): il dev server proxya /api verso uvicorn, così
    // non serve configurare VITE_API_BASE_URL per lo sviluppo locale.
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
