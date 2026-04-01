const ACCESS_TOKEN_KEY = 'segmentation_access_token'
const ACCESS_EXPIRES_AT_KEY = 'segmentation_access_expires_at'

export const AUTH_UNAUTHORIZED_EVENT = 'app:auth-unauthorized'

const canUseStorage = () => typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'

export const getAccessToken = (): string => {
  if (!canUseStorage()) {
    return ''
  }
  return window.localStorage.getItem(ACCESS_TOKEN_KEY) || ''
}

export const getAccessExpiresAt = (): number | null => {
  if (!canUseStorage()) {
    return null
  }
  const raw = window.localStorage.getItem(ACCESS_EXPIRES_AT_KEY)
  if (!raw) {
    return null
  }
  const expiresAt = Number(raw)
  return Number.isFinite(expiresAt) ? expiresAt : null
}

export const setAuthSession = (accessToken: string, expiresInSeconds: number) => {
  if (!canUseStorage()) {
    return
  }
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  if (expiresInSeconds > 0) {
    const expiresAt = Date.now() + expiresInSeconds * 1000
    window.localStorage.setItem(ACCESS_EXPIRES_AT_KEY, String(expiresAt))
  } else {
    window.localStorage.removeItem(ACCESS_EXPIRES_AT_KEY)
  }
}

export const clearAuthStorage = () => {
  if (!canUseStorage()) {
    return
  }
  window.localStorage.removeItem(ACCESS_TOKEN_KEY)
  window.localStorage.removeItem(ACCESS_EXPIRES_AT_KEY)
}

export const hasValidAccessToken = () => {
  const token = getAccessToken()
  if (!token) {
    return false
  }
  const expiresAt = getAccessExpiresAt()
  if (!expiresAt) {
    return true
  }
  return expiresAt > Date.now()
}

const decodeJwtPayload = (token: string): Record<string, unknown> | null => {
  const parts = token.split('.')
  if (parts.length !== 3) {
    return null
  }

  try {
    const payload = parts[1]
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4)
    const decoded = atob(padded)
    return JSON.parse(decoded) as Record<string, unknown>
  } catch {
    return null
  }
}

export const getAccessTokenRole = (): string | null => {
  const token = getAccessToken()
  if (!token) {
    return null
  }
  const payload = decodeJwtPayload(token)
  const role = payload?.role
  return typeof role === 'string' ? role : null
}
