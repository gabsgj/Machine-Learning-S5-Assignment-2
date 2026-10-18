import { useEffect, useState } from 'react'
import { ArrowDown, ArrowRight, Layers3, RotateCcw, Workflow } from 'lucide-react'
import { api } from '../services/api'
import type { Capability, CompositionResult, Scenario } from '../types'
import { FeatureVectorView } from '../components/FeatureVector'
import { CapabilityDetails } from '../components/CapabilityDetails'
import { MetricCard, PageHeading, Panel, Pill } from '../components/Primitives'
import type { Notify } from './types'

export function CompositionPage({ scenario, notify }: { scenario: Scenario; notify: Notify }) {
  const defaultChain = scenario.capabilities.slice(0, 3).map((item) => item.id)
  const [chainIds, setChainIds] = useState(defaultChain)
  const [result, setResult] = useState<CompositionResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [showVector, setShowVector] = useState(true)
  const selected = chainIds.map((id) => scenario.capabilities.find((item) => item.id === id)).filter((item): item is Capability => Boolean(item))

  useEffect(() => { setChainIds(scenario.capabilities.slice(0, 3).map((item) => item.id)); setResult(null) }, [scenario.id, scenario.capabilities])

  function toggle(id: string) {
    setChainIds((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id])
    setResult(null)
  }

  async function build() {
    if (selected.length < 2) return
    setBusy(true); setResult(null)
    try { setResult(await api.compose(selected)); notify('Composite capability constructed by the backend.', 'success') }
    catch (error) { notify((error as Error).message, 'error') }
    finally { setBusy(false) }
  }

  return <>
    <PageHeading eyebrow="EXPLORE / COMPOSITION" title="Build a capability chain" description="Select an ordered sequence, validate each handoff, and inspect the resulting composite capability and vector." action={<Pill tone="blue">Ordered composition</Pill>} />
    <Panel className="chain-builder"><div className="panel-heading"><span className="panel-icon"><Workflow size={17} /></span><div><h3>Choose components in execution order</h3><p>Click to add; selected capabilities form the chain from left to right.</p></div><button className="button button-primary push-right" onClick={build} disabled={busy || selected.length < 2}>{busy ? <RotateCcw className="spin" size={15} /> : <Layers3 size={15} />}Compose chain</button></div>
      <div className="chain-selection">{scenario.capabilities.map((capability) => {
        const position = chainIds.indexOf(capability.id)
        return <button key={capability.id} className={`chain-option ${position >= 0 ? 'chosen' : ''}`} onClick={() => toggle(capability.id)}><span className="chain-number">{position >= 0 ? position + 1 : '+'}</span><div><strong>{capability.name}</strong><small>{capability.type} · {capability.id}</small></div><span className="chain-select-mark">{position >= 0 ? 'Selected' : 'Add'}</span></button>
      })}</div>
      <div className="chain-preview"><span className="eyebrow">CURRENT ORDER · {selected.length} COMPONENTS</span><div className="chain-preview-items">{selected.length ? selected.map((item, index) => <div className="chain-preview-item" key={item.id}><div><small>{index + 1}</small><strong>{item.name}</strong></div>{index < selected.length - 1 && <ArrowRight size={17} />}</div>) : <span className="muted-note">Choose at least two capabilities.</span>}</div></div>
    </Panel>

    {result && <>
      <div className="composition-outcome"><div className="outcome-mark"><Layers3 size={21} /></div><div className="outcome-copy"><span className="eyebrow">COMPOSITE CAPABILITY</span><h2>{result.composite.name}</h2><p>{result.composite.components.join(' → ')}</p></div><Pill tone="green">{result.compatibility_checks.length} handoffs validated</Pill></div>
      <div className="metric-grid four-cols composition-metrics">
        <MetricCard label="Vector dimensions" value={result.dimension_count} hint="Generated from composite" />
        <MetricCard label="Reliability" value={`${(result.composite.reliability * 100).toFixed(2)}%`} hint="Product across stages" />
        <MetricCard label="Availability" value={`${(result.composite.availability * 100).toFixed(2)}%`} hint="Product across stages" />
        <MetricCard label="Execution time" value={`${result.composite.cost.time_ms} ms`} hint={`Cost ${result.composite.cost.money}`} />
      </div>
      <Panel className="handoff-panel"><div className="panel-heading"><span className="panel-icon"><ArrowRight size={17} /></span><div><h3>Validated handoffs</h3><p>Evidence returned by the backend compatibility checks</p></div></div>
        <div className="handoff-list">{result.compatibility_checks.map((check, index) => <div className="handoff-check" key={`${check.producer_id}-${check.consumer_id}`}><div className="handoff-title"><strong>{check.producer_id}</strong><ArrowRight size={15} /><strong>{check.consumer_id}</strong><Pill tone={check.compatible ? 'green' : 'red'}>{check.compatible ? 'compatible' : 'blocked'}</Pill></div><div className="handoff-evidence">{check.evidence.map((row, itemIndex) => <span key={itemIndex} className={row.satisfied ? 'evidence-pass' : 'evidence-fail'}>{row.satisfied ? '✓' : '×'} {String(row.requirement)} · {String(row.name)}</span>)}</div>{index < result.compatibility_checks.length - 1 && <div className="flow-stem"><ArrowDown size={14} /></div>}</div>)}</div>
      </Panel>
      <CapabilityDetails capability={result.composite} />
      <Panel className="composite-vector-panel"><div className="panel-heading"><span className="panel-icon"><Layers3 size={17} /></span><div><h3>Composite representation</h3><p>Vector encoded by the same backend feature function as atomic capabilities</p></div><button className="text-button push-right" onClick={() => setShowVector((open) => !open)}>{showVector ? 'Collapse' : 'Expand'}</button></div>{showVector && <FeatureVectorView vector={result.embedding} />}</Panel>
    </>}
  </>
}
