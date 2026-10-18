import { useCallback, useEffect, useRef, useState } from 'react'

export type NotificationTone = 'success' | 'error' | 'info'
export type Notification = { id: number; message: string; tone: NotificationTone }

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const timers = useRef(new Map<number, number>())

  const dismiss = useCallback((id: number) => {
    setNotifications((current) => current.filter((notification) => notification.id !== id))
    const timer = timers.current.get(id)
    if (timer !== undefined) {
      window.clearTimeout(timer)
      timers.current.delete(id)
    }
  }, [])

  const notify = useCallback((message: string, tone: NotificationTone = 'info') => {
    const id = Date.now() + Math.random()
    setNotifications((current) => [...current.slice(-2), { id, message, tone }])
    const timer = window.setTimeout(() => dismiss(id), 5200)
    timers.current.set(id, timer)
  }, [dismiss])

  useEffect(() => () => {
    timers.current.forEach((timer) => window.clearTimeout(timer))
    timers.current.clear()
  }, [])

  return { notifications, notify, dismiss }
}
