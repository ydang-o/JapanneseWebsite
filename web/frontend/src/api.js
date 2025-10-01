const API_BASE = '/api'

export function setAuthToken(token) {
  if (token) localStorage.setItem('token', token)
  else localStorage.removeItem('token')
}

export function getAuthToken() {
  return localStorage.getItem('token') || ''
}

export async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {})
  const token = getAuthToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (!headers.has('Content-Type') && options.body) headers.set('Content-Type', 'application/json')

  const resp = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })
  if (!resp.ok) {
    let errorText
    try {
      const data = await resp.json()
      errorText = data?.error || resp.statusText
    } catch {
      errorText = resp.statusText
    }
    throw new Error(errorText)
  }
  const contentType = resp.headers.get('Content-Type') || ''
  if (contentType.includes('application/json')) return resp.json()
  return resp.text()
} 