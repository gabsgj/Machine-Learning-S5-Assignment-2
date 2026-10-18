import { ArrowRight, Boxes, CircleDot, Compass, Target, Workflow } from 'lucide-react'
import type { Goal, Scenario, State } from '../types'
import type { PageId } from '../components/Sidebar'
import { MetricCard, PageHeading, Panel, Pill } from '../components/Primitives'

function ValueList({ values }: { values: Record<string, unknown> }) {
  return <div className="value-list">{Object.entries(values).map(([key, value]) => <div key={key}><span>{key}</span><code>{JSON.stringify(value)}</code></div>)}</div>
}

export function OverviewPage({ scenario, onNavigate }: { scenario: Scenario; onNavigate: (page: PageId) => void }) {
  const state = scenario.states[0]
  const goal = scenario.goals[0]
  return <>
    <PageHeading eyebrow="WORKSPACE / OVERVIEW" title="Capability landscape" description="A formal view of the scenario, its desired outcomes, and the operations that can change application state." action={<Pill tone="blue">Formal scenario</Pill>} />
    <div className="metric-grid four-cols">
      <MetricCard label="Application states" value={scenario.states.length} hint="Declared snapshots" icon={CircleDot} />
      <MetricCard label="Goal specifications" value={scenario.goals.length} hint="Desired conditions" icon={Target} />
      <MetricCard label="Capabilities" value={scenario.capabilities.length} hint="Available operations" icon={Boxes} />
      <MetricCard label="Composition chains" value="—" hint="Built interactively" icon={Workflow} />
    </div>
    <div className="overview-grid">
      <Panel className="overview-state"><div className="panel-heading"><span className="panel-icon"><CircleDot size={17} /></span><div><h3>Initial state</h3><p>{state?.id ?? 'No state selected'} · named values</p></div><button className="text-button push-right" onClick={() => onNavigate('capabilities')}>Inspect <ArrowRight size={14} /></button></div>
        {state ? <ValueList values={state.values} /> : <div className="blank-message">Add a state in Scenario editor to get started.</div>}
      </Panel>
      <Panel className="overview-goal"><div className="panel-heading"><span className="panel-icon goal-icon"><Target size={17} /></span><div><h3>Goal conditions</h3><p>{goal?.id ?? 'No goal selected'} · formal predicates</p></div><button className="text-button push-right" onClick={() => onNavigate('relationships')}>Analyze <ArrowRight size={14} /></button></div>
        {goal ? <PredicateRows goal={goal} /> : <div className="blank-message">Add a goal specification in Scenario editor.</div>}
      </Panel>
    </div>
    <Panel className="capability-overview"><div className="panel-heading"><span className="panel-icon"><Compass size={17} /></span><div><h3>Available capabilities</h3><p>Operations, mechanisms, and declared state effects</p></div><button className="text-button push-right" onClick={() => onNavigate('capabilities')}>Open explorer <ArrowRight size={14} /></button></div>
      <div className="capability-table"><div className="table-head"><span>CAPABILITY</span><span>TYPE</span><span>OUTPUT EFFECTS</span><span>RELIABILITY</span><span>AVAILABILITY</span></div>
        {scenario.capabilities.slice(0, 6).map((capability) => <div className="table-row" key={capability.id}>
          <div><strong>{capability.name}</strong><small>{capability.id}</small></div><Pill tone={capability.type === 'API' ? 'blue' : 'neutral'}>{capability.type}</Pill>
          <div className="effect-summary">{capability.effects.length ? capability.effects.map((item) => `${item.name} ${item.operator} ${String(item.value)}`).join(' · ') : 'No state effects'}</div>
          <div className="table-number">{(capability.reliability * 100).toFixed(1)}%</div><div className="table-number">{(capability.availability * 100).toFixed(1)}%</div>
        </div>)}
      </div>
    </Panel>
    <div className="scope-note"><span className="scope-dot" /><span><strong>Representation before orchestration.</strong> This workspace compares formal operation signatures and builds composites. It does not search for execution plans.</span></div>
  </>
}

function PredicateRows({ goal }: { goal: Goal }) {
  return <div className="goal-conditions">{goal.conditions.map((item, index) => <div className="goal-condition" key={`${item.name}-${index}`}><span className="condition-check"><Target size={13} /></span><span>{item.name}</span><code>{item.operator} {JSON.stringify(item.value)}</code></div>)}</div>
}

export function StateCard({ state }: { state: State }) {
  return <ValueList values={state.values} />
}
