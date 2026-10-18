import { useCallback, useState } from 'react'

export function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  if (typeof error === 'string' && error) return error
  return 'The request could not be completed.'
}

/**
 * Keeps the loading/error behavior for API actions consistent across pages.
 * The operation itself remains with the page so its result can update local UI state.
 */
type AsyncActionOptions = { trackBusy?: boolean }

export function useAsyncAction(onError: (message: string) => void) {
  const [busy, setBusy] = useState(false)

  const run = useCallback(async <T,>(operation: () => Promise<T>, options: AsyncActionOptions = {}): Promise<T | undefined> => {
    const trackBusy = options.trackBusy ?? true
    if (trackBusy) setBusy(true)
    try {
      return await operation()
    } catch (error) {
      onError(errorMessage(error))
      return undefined
    } finally {
      if (trackBusy) setBusy(false)
    }
  }, [onError])

  return { busy, run }
}
