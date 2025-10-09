const API_BASE = '/api'

function dispatchAuthEvent(name, detail) {
  if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function') {
    window.dispatchEvent(new CustomEvent(name, { detail }))
    if (name !== 'auth-state-changed') {
      window.dispatchEvent(new CustomEvent('auth-state-changed', { detail }))
    }
  }
}

export function setAuthToken(token) {
  if (token) localStorage.setItem('token', token)
  else localStorage.removeItem('token')
  dispatchAuthEvent('auth-token-changed', token || '')
  dispatchAuthEvent('auth-state-changed', { token: token || '', role: getUserRole() })
}

export function getAuthToken() {
  return localStorage.getItem('token') || ''
}

export function setUserRole(role) {
  if (role) localStorage.setItem('userRole', role)
  else localStorage.removeItem('userRole')
  dispatchAuthEvent('auth-role-changed', role || '')
  dispatchAuthEvent('auth-state-changed', { token: getAuthToken(), role: role || '' })
}

export function getUserRole() {
  return localStorage.getItem('userRole') || ''
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