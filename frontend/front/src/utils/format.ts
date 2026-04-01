export function resolveAssetUrl(url: string): string {
  if (!url) {
    return ''
  }

  if (/^https?:\/\//.test(url) || url.startsWith('blob:') || url.startsWith('data:')) {
    return url
  }

  const base = import.meta.env.VITE_FILE_BASE_URL || import.meta.env.VITE_API_BASE_URL || ''

  if (!base) {
    return url
  }

  try {
    return new URL(url, base).toString()
  } catch {
    return url
  }
}

export function formatMs(seconds: number): string {
  return `${(seconds * 1000).toFixed(2)} ms`
}
