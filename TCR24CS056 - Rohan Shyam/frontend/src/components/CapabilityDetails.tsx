import { Box, Braces, Gauge, ShieldCheck, Workflow } from 'lucide-react'
import type { Capability, Predicate } from '../types'
import { Panel } from './Primitives'

function PredicateList({ title, items }: { title: string; items: Predicate[] }) {
  return <div className="detail-block"><div className="detail-label">{title}<span>{items.length}</span></div>
    {items.length ? <ul className="token-list">{items.map((item, index) => <li key={`${item.name}-${index}`}><code>{item.name} {item.operator} {JSON.stringify(item.value)}</code></li>)}</ul> : <span className="muted-note">None declared</span>}
  </div>
}

export function CapabilityDetails({ capability }: { capability: Capability }) {
  return <div className="details-grid">
    <Panel className="detail-panel"><div className="panel-heading"><span className="panel-icon"><Braces size={17} /></span><div><h3>Interface</h3><p>Typed values crossing the capability boundary</p></div></div>
      <div className="io-columns"><div><div className="detail-label">Inputs <span>{capability.inputs.length}</span></div>{capability.inputs.length ? capability.inputs.map((item) => <div className="io-item" key={`in-${item.name}`}><span className="io-dot in-dot" /><div><strong>{item.name}</strong><small>{item.type}{item.domain ? ` · ${item.domain}` : ''}{item.required ? ' · required' : ' · optional'}</small></div></div>) : <span className="muted-note">No inputs</span>}</div>
        <div><div className="detail-label">Outputs <span>{capability.outputs.length}</span></div>{capability.outputs.length ? capability.outputs.map((item) => <div className="io-item" key={`out-${item.name}`}><span className="io-dot out-dot" /><div><strong>{item.name}</strong><small>{item.type}{item.domain ? ` · ${item.domain}` : ''}</small></div></div>) : <span className="muted-note">No outputs</span>}</div></div>
    </Panel>
    <Panel className="detail-panel"><div className="panel-heading"><span className="panel-icon"><Workflow size={17} /></span><div><h3>State transformation</h3><p>When it can run and what it changes</p></div></div>
      <div className="predicate-columns"><PredicateList title="Preconditions" items={capability.preconditions} /><PredicateList title="Effects" items={capability.effects} /></div>
      <PredicateList title="Constraints" items={capability.constraints} />
    </Panel>
    <Panel className="detail-panel"><div className="panel-heading"><span className="panel-icon"><Box size={17} /></span><div><h3>Execution</h3><p>Mechanism and required resources</p></div></div>
      <div className="mechanism-list">{Object.entries(capability.mechanism).map(([key, value]) => <div key={key}><span>{key}</span><code>{value}</code></div>)}</div>
      <div className="detail-label spaced-label">Resources</div><div className="resource-list">{capability.resources.length ? capability.resources.map((item) => <span className="resource-chip" key={item}>{item}</span>) : <span className="muted-note">None declared</span>}</div>
    </Panel>
    <Panel className="detail-panel"><div className="panel-heading"><span className="panel-icon"><Gauge size={17} /></span><div><h3>Operational profile</h3><p>Quality values carried separately in the vector</p></div></div>
      <div className="operational-grid"><div><span>Time</span><strong>{capability.cost.time_ms} ms</strong></div><div><span>Cost</span><strong>{capability.cost.money}</strong></div><div><span>Resources</span><strong>{capability.cost.resource}</strong></div><div><span>Risk</span><strong>{capability.cost.risk}</strong></div><div><span>Energy</span><strong>{capability.cost.energy}</strong></div><div><span>Reliability</span><strong>{(capability.reliability * 100).toFixed(1)}%</strong></div><div><span>Availability</span><strong>{(capability.availability * 100).toFixed(1)}%</strong></div></div>
      <div className="availability-track"><i style={{ width: `${capability.availability * 100}%` }} /></div>
      <div className="operational-foot"><ShieldCheck size={14} />Reliability and availability are distinct measures</div>
    </Panel>
  </div>
}
