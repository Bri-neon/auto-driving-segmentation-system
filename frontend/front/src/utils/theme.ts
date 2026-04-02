export type ThemeKey = 'light' | 'dark' | 'ocean' | 'emerald' | 'sunset'

export interface ThemeOption {
  key: ThemeKey
  label: string
  description: string
  preview: string
}

const THEME_STORAGE_KEY = 'auto_seg_theme'
const DEFAULT_THEME: ThemeKey = 'light'

export const THEME_OPTIONS: ThemeOption[] = [
  {
    key: 'light',
    label: 'Light',
    description: 'Default blue-white glass style',
    preview: 'linear-gradient(120deg, #eaf4ff 0%, #d8eaff 100%)',
  },
  {
    key: 'dark',
    label: 'Dark',
    description: 'Low-brightness dark interface',
    preview: 'linear-gradient(120deg, #0d1118 0%, #1a2333 100%)',
  },
  {
    key: 'ocean',
    label: 'Ocean',
    description: 'Cool blue-cyan tech palette',
    preview: 'linear-gradient(120deg, #d7efff 0%, #c4ddff 100%)',
  },
  {
    key: 'emerald',
    label: 'Emerald',
    description: 'Fresh mint-green atmosphere',
    preview: 'linear-gradient(120deg, #e4f8f2 0%, #cdeee1 100%)',
  },
  {
    key: 'sunset',
    label: 'Sunset',
    description: 'Warm highlight-focused palette',
    preview: 'linear-gradient(120deg, #fff3e7 0%, #ffe3cd 100%)',
  },
]

const isThemeKey = (value: string): value is ThemeKey => THEME_OPTIONS.some((item) => item.key === value)

const getStorage = () => {
  if (typeof window === 'undefined') {
    return null
  }
  try {
    return window.localStorage
  } catch {
    return null
  }
}

export const getStoredTheme = (): ThemeKey => {
  const storage = getStorage()
  const raw = storage?.getItem(THEME_STORAGE_KEY)
  if (raw && isThemeKey(raw)) {
    return raw
  }
  return DEFAULT_THEME
}

const setStoredTheme = (theme: ThemeKey) => {
  const storage = getStorage()
  if (storage) {
    storage.setItem(THEME_STORAGE_KEY, theme)
  }
}

const applyThemeToDom = (theme: ThemeKey) => {
  if (typeof document === 'undefined') {
    return
  }
  document.documentElement.setAttribute('data-theme', theme)
}

export const initTheme = (): ThemeKey => {
  const theme = getStoredTheme()
  applyThemeToDom(theme)
  return theme
}

export const setTheme = (theme: ThemeKey): ThemeKey => {
  applyThemeToDom(theme)
  setStoredTheme(theme)
  return theme
}

export const getActiveTheme = (): ThemeKey => {
  if (typeof document !== 'undefined') {
    const current = document.documentElement.getAttribute('data-theme')
    if (current && isThemeKey(current)) {
      return current
    }
  }
  return getStoredTheme()
}
