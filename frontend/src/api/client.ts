// Stringa vuota = stesso host/porta della pagina (nginx fa da reverse proxy
// verso il backend su /api, vedi frontend/nginx.conf). In dev locale senza
// Docker, VITE_API_BASE_URL punta invece direttamente a uvicorn.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    // Il cookie di sessione (vedi backend/app/core/auth.py) va sempre
    // inviato — 'include' invece del default 'same-origin' perché in dev
    // locale VITE_API_BASE_URL può puntare a un'origine diversa (uvicorn
    // su :8000 invece del proxy di vite), dove 'same-origin' non lo
    // manderebbe affatto.
    credentials: 'include',
    ...init,
  })
  if (response.status === 401 && path !== '/api/auth/login') {
    // Sessione scaduta o mai fatta: AuthGate (vedi App.tsx) intercetta
    // questo evento e mostra subito la pagina di login, senza dover
    // ricaricare tutta la pagina per scoprirlo.
    window.dispatchEvent(new Event('homehub:unauthorized'))
  }
  if (!response.ok) {
    throw new Error(`Richiesta fallita (${response.status}): ${path}`)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return response.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
