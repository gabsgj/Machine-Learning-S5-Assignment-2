import { Check, CircleAlert, LoaderCircle, type LucideIcon } from 'lucide-react'
import { useId, type ReactNode } from 'react'

export function Panel({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={`panel ${className}`}>{children}</section>
}

export function PageHeading({ eyebrow, title, description, action }: {
  eyebrow: string; title: string; description: string; action?: ReactNode
}) {
  return <header className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action && <div className="heading-action">{action}</div>}</header>
}

export function Pill({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'green' | 'red' | 'blue' | 'amber' }) {
  return <span className={`pill pill-${tone}`}>{children}</span>
}

export function MetricCard({ label, value, hint, icon: Icon }: { label: string; value: string | number; hint?: string; icon?: LucideIcon }) {
  return <div className="metric-card"><div className="metric-top"><span>{label}</span>{Icon && <Icon size={17} />}</div><strong>{value}</strong>{hint && <small>{hint}</small>}</div>
}

export function SelectField({ label, value, onChange, children }: {
  label: string; value: string; onChange: (value: string) => void; children: ReactNode
}) {
  const id = useId()
  return <label className="field" htmlFor={id}><span>{label}</span><select id={id} value={value} onChange={(event) => onChange(event.target.value)}>{children}</select></label>
}

export function Loading({ label = 'Loading' }: { label?: string }) {
  return <span className="loading" role="status" aria-live="polite"><LoaderCircle className="spin" size={17} aria-hidden="true" />{label}</span>
}

export function Notice({ children, tone = 'info' }: { children: ReactNode; tone?: 'info' | 'error' | 'success' }) {
  const Icon = tone === 'error' ? CircleAlert : Check
  return <div className={`notice notice-${tone}`} role={tone === 'error' ? 'alert' : 'status'}><Icon size={17} aria-hidden="true" /><span>{children}</span></div>
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return <div className="empty-state"><div className="empty-mark">·</div><strong>{title}</strong><p>{description}</p></div>
}
