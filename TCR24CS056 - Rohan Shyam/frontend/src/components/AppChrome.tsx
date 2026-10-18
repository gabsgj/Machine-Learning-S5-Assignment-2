import { Bell, CircleAlert, CircleCheck, ExternalLink, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import type { Notification } from '../hooks/useNotifications'
import type { Scenario } from '../types'
import { api } from '../services/api'

export function AppLoadingScreen() {
  return <div className="app-loading" role="status" aria-live="polite">
    <div className="brand-mark large"><span className="brand-glyph">C</span></div>
    <strong>Opening Capability Composition</strong>
    <span>Connecting to the local embedding service…</span>
  </div>
}

export function ConnectionScreen({ error, onRetry }: { error: string | null; onRetry: () => void }) {
  return <div className="connection-screen" role="alert">
    <div className="connection-icon"><WifiOff size={23} /></div>
    <span className="eyebrow">BACKEND CONNECTION</span>
    <h1>Could not load the scenario</h1>
    <p>{error ?? 'The API did not return a scenario.'}</p>
    <div className="connection-url">Expected API at <code>{api.baseUrl}</code></div>
    <button type="button" className="button button-primary" onClick={onRetry}><RefreshCw size={15} />Retry connection</button>
    <a href={`${api.baseUrl}/docs`} target="_blank" rel="noreferrer">Open API documentation <ExternalLink size={13} /></a>
  </div>
}

export function AppHeader({ scenario, backendOnline }: { scenario: Scenario; backendOnline: boolean }) {
  return <header className="topbar">
    <div className="breadcrumb"><span>CAPABILITY COMPOSITION</span><b>/</b><strong>{scenario.name}</strong></div>
    <div className="topbar-right">
      <a className="api-link" href={`${api.baseUrl}/docs`} target="_blank" rel="noreferrer">API docs <ExternalLink size={13} /></a>
      <span className={`connection-status ${backendOnline ? 'online' : 'offline'}`} role="status">
        <i />{backendOnline ? <><Wifi size={14} /> API connected</> : <><WifiOff size={14} /> API disconnected</>}
      </span>
      <button type="button" className="icon-button" aria-label="Notifications"><Bell size={16} /></button>
    </div>
  </header>
}

export function ToastViewport({ notifications, onDismiss }: { notifications: Notification[]; onDismiss: (id: number) => void }) {
  return <div className="toast-stack" aria-live="polite" aria-atomic="false">
    {notifications.map((notification) => <div className={`toast toast-${notification.tone}`} key={notification.id} role={notification.tone === 'error' ? 'alert' : 'status'}>
      {notification.tone === 'error' ? <CircleAlert size={17} /> : <CircleCheck size={17} />}
      <span>{notification.message}</span>
      <button type="button" aria-label="Dismiss notification" onClick={() => onDismiss(notification.id)}>×</button>
    </div>)}
  </div>
}
