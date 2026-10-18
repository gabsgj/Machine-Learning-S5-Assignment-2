import { useCallback, useEffect, useState } from 'react'
import { AppHeader, AppLoadingScreen, ConnectionScreen, ToastViewport } from './components/AppChrome'
import { PageContent } from './components/PageContent'
import { Sidebar, type PageId } from './components/Sidebar'
import { useNotifications } from './hooks/useNotifications'
import { errorMessage } from './hooks/useAsyncAction'
import { api } from './services/api'
import type { Scenario } from './types'

export default function App() {
  const [page, setPage] = useState<PageId>('overview')
  const [scenario, setScenario] = useState<Scenario | null>(null)
  const [backendOnline, setBackendOnline] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [loadedExample, setLoadedExample] = useState<string | null>(null)
  const [experimentRequest, setExperimentRequest] = useState(0)
  const { notifications, notify, dismiss } = useNotifications()

  const load = useCallback(async (showSpinner = true) => {
    if (showSpinner) setLoading(true)
    try {
      const [health, loadedScenario] = await Promise.all([api.health(), api.getScenario()])
      setBackendOnline(health.status === 'ok')
      setScenario(loadedScenario)
      setLoadError(null)
    } catch (error) {
      setBackendOnline(false)
      setLoadError(errorMessage(error))
    } finally {
      setLoading(false)
    }
  }, [])

  const loadExample = useCallback(async (example: Scenario, name: string) => {
    try {
      const saved = await api.saveScenario(example)
      setScenario(saved)
      setLoadedExample(name)
      setPage('experiments')
      setExperimentRequest((current) => current + 1)
      notify(`${name} loaded. Experiments are running.`, 'success')
    } catch (error) {
      notify(errorMessage(error), 'error')
    }
  }, [notify])

  useEffect(() => {
    void load()
    const timer = window.setInterval(() => {
      void api.health().then(() => setBackendOnline(true)).catch(() => setBackendOnline(false))
    }, 25000)
    return () => window.clearInterval(timer)
  }, [load])

  if (loading) return <AppLoadingScreen />
  if (!scenario) return <ConnectionScreen error={loadError} onRetry={() => void load()} />

  return <div className="app-shell">
    <Sidebar active={page} onChange={setPage} />
    <div className="main-shell">
      <AppHeader scenario={scenario} backendOnline={backendOnline} />
      <PageContent
        page={page}
        scenario={scenario}
        notify={notify}
        onNavigate={setPage}
        onScenario={setScenario}
        onLoadExample={loadExample}
        loadedExample={loadedExample}
        experimentRequest={experimentRequest}
      />
    </div>
    <ToastViewport notifications={notifications} onDismiss={dismiss} />
  </div>
}
