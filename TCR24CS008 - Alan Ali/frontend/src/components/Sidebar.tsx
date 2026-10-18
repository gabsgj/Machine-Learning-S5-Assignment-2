import { Activity, Boxes, ChartNoAxesCombined, GitBranch, Layers3, Settings2, Workflow } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export type PageId = 'overview' | 'capabilities' | 'relationships' | 'composition' | 'experiments' | 'scenario'
const links: Array<{ id: PageId; label: string; icon: LucideIcon; group: string }> = [
  { id: 'overview', label: 'Overview', icon: Activity, group: 'WORKSPACE' },
  { id: 'capabilities', label: 'Capabilities', icon: Boxes, group: 'EXPLORE' },
  { id: 'relationships', label: 'Relationships', icon: GitBranch, group: 'EXPLORE' },
  { id: 'composition', label: 'Composition', icon: Workflow, group: 'EXPLORE' },
  { id: 'experiments', label: 'Experiments', icon: ChartNoAxesCombined, group: 'EVALUATE' },
  { id: 'scenario', label: 'Scenario editor', icon: Settings2, group: 'WORKSPACE' },
]

export function Sidebar({ active, onChange }: { active: PageId; onChange: (id: PageId) => void }) {
  const groups = [...new Set(links.map((link) => link.group))]
  return <aside className="sidebar">
    <div className="brand"><div className="brand-mark"><Layers3 size={19} /></div><div className="brand-copy"><strong>Capability Composition</strong></div></div>
    <div className="sidebar-rule" />
    <nav aria-label="Main navigation">{groups.map((group) => <div className="nav-group" key={group}><div className="nav-label">{group}</div>
      {links.filter((link) => link.group === group).map(({ id, label, icon: Icon }) => <button key={id} className={`nav-item ${active === id ? 'active' : ''}`} onClick={() => onChange(id)}><Icon size={17} /><span>{label}</span>{active === id && <i />}</button>)}
    </div>)}</nav>
  </aside>
}
