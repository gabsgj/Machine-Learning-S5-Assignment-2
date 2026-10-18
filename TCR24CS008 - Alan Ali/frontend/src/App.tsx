import { useCallback, useEffect, useState } from 'react'
import { Bell, CircleAlert, CircleCheck, ExternalLink, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import { Sidebar, type PageId } from './components/Sidebar'
import { CapabilitiesPage } from './pages/CapabilitiesPage'
import { CompositionPage } from './pages/CompositionPage'
import { ExperimentsPage } from './pages/ExperimentsPage'
import { OverviewPage } from './pages/OverviewPage'
import { RelationshipsPage } from './pages/RelationshipsPage'
import { ScenarioPage } from './pages/ScenarioPage'
import { api } from './services/api'
import type { Scenario } from './types'

type Toast = { id: number; message: string; tone: 'success' | 'error' | 'info' }

export default function App() {
  const [page, setPage] = useState<PageId>('overview')
  const [scenario, setScenario] = useState<Scenario | null>(null)
  const [backendOnline, setBackendOnline] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [toasts, setToasts] = useState<Toast[]>([])
  const [loadedExample, setLoadedExample] = useState<string | null>(null)
  const [experimentRequest, setExperimentRequest] = useState(0)

  const notify = useCallback((message: string, tone: Toast['tone'] = 'info') => {
    const id = Date.now() + Math.random()
    setToasts((current) => [...current.slice(-2), { id, message, tone }])
    window.setTimeout(() => setToasts((current) => current.filter((toast) => toast.id !== id)), 5200)
  }, [])

  const load = useCallback(async (showSpinner = true) => {
    if (showSpinner) setLoading(true)
    try {
      const [health, loadedScenario] = await Promise.all([api.health(), api.getScenario()])
      setBackendOnline(health.status === 'ok'); setScenario(loadedScenario); setLoadError(null)
    } catch (error) {
      setBackendOnline(false); setLoadError((error as Error).message)
    } finally { setLoading(false) }
  }, [])

  const loadExample = useCallback(async (example: Scenario, name: string) => {
    try {
      const saved = await api.saveScenario(example)
      setScenario(saved); setLoadedExample(name); setPage('experiments'); setExperimentRequest((current) => current + 1)
      notify(`${name} loaded. Experiments are running.`, 'success')
    } catch (error) { notify((error as Error).message, 'error') }
  }, [notify])

  useEffect(() => { void load(); const timer = window.setInterval(() => { void api.health().then(() => setBackendOnline(true)).catch(() => setBackendOnline(false)) }, 25000); return () => window.clearInterval(timer) }, [load])

  if (loading) return <div className="app-loading"><div className="brand-mark large"><span className="brand-glyph">C</span></div><strong>Opening Capability Composition</strong><span>Connecting to the local embedding service…</span></div>
  if (!scenario) return <div className="connection-screen"><div className="connection-icon"><WifiOff size={23} /></div><span className="eyebrow">BACKEND CONNECTION</span><h1>Could not load the scenario</h1><p>{loadError ?? 'The API did not return a scenario.'}</p><div className="connection-url">Expected API at <code>{api.baseUrl}</code></div><button className="button button-primary" onClick={() => void load()}><RefreshCw size={15} />Retry connection</button><a href={`${api.baseUrl}/docs`} target="_blank" rel="noreferrer">Open API documentation <ExternalLink size={13} /></a></div>

  return <div className="app-shell">
    <Sidebar active={page} onChange={setPage} />
    <div className="main-shell">
      <header className="topbar"><div className="breadcrumb"><span>CAPABILITY COMPOSITION</span><b>/</b><strong>{scenario.name}</strong></div><div className="topbar-right"><a className="api-link" href={`${api.baseUrl}/docs`} target="_blank" rel="noreferrer">API docs <ExternalLink size={13} /></a><span className={`connection-status ${backendOnline ? 'online' : 'offline'}`}><i />{backendOnline ? <><Wifi size={14} /> API connected</> : <><WifiOff size={14} /> API disconnected</>}</span><button className="icon-button" aria-label="Notifications"><Bell size={16} /></button></div></header>
      <main className="page-content" key={page}>
        {page === 'overview' && <OverviewPage scenario={scenario} onNavigate={setPage} />}
        {page === 'capabilities' && <CapabilitiesPage scenario={scenario} notify={notify} />}
        {page === 'relationships' && <RelationshipsPage scenario={scenario} notify={notify} />}
        {page === 'composition' && <CompositionPage scenario={scenario} notify={notify} />}
        {page === 'experiments' && <ExperimentsPage scenario={scenario} notify={notify} autoRunToken={experimentRequest} />}
        {page === 'scenario' && <ScenarioPage scenario={scenario} onScenario={setScenario} notify={notify} onLoadExample={loadExample} loadedExample={loadedExample} />}
        <footer className="page-footer"><span>Capability Composition</span><span>Formal feature vectors · Backend-computed results</span></footer>
      </main>
    </div>
    <div className="toast-stack" aria-live="polite">{toasts.map((toast) => <div className={`toast toast-${toast.tone}`} key={toast.id}>{toast.tone === 'error' ? <CircleAlert size={17} /> : <CircleCheck size={17} />}<span>{toast.message}</span><button onClick={() => setToasts((items) => items.filter((item) => item.id !== toast.id))}>×</button></div>)}</div>
  </div>
}
