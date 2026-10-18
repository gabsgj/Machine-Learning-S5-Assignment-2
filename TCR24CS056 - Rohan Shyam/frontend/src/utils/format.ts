export function pretty(value: unknown): string {
  return JSON.stringify(value, null, 2)
}

export function score(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

export function title(value: string): string {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export function featureGroup(key: string): string {
  return key.split(':', 1)[0] ?? 'other'
}
