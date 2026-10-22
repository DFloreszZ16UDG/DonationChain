const API_URL = import.meta.env.VITE_API_URL ?? '/api'

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('donationchain_token')
  const headers = new Headers(options.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')

  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: 'Error inesperado' }))
    const detail = Array.isArray(body.detail)
      ? body.detail.map((item: { msg: string }) => item.msg).join('. ')
      : body.detail
    throw new ApiError(response.status, detail || 'No fue posible completar la operación')
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export function money(value: string | number) {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
  }).format(Number(value))
}

export function shortHash(value: string | null, length = 12) {
  if (!value) return 'Sin anclaje'
  return `${value.slice(0, length)}…${value.slice(-6)}`
}
