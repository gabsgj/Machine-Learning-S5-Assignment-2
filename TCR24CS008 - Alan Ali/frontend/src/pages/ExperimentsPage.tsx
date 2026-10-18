import { useEffect, useState } from 'react'
import { Activity, AlertTriangle, CheckCircle2, FlaskConical, RefreshCw } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../services/api'
import type { ExperimentReport, Scenario } from '../types'
import type { Notify } from './types'
import { EmptyState, Loading, MetricCard, PageHeading, Panel, Pill } from '../components/Primitives'
import { title } from '../utils/format'

export function ExperimentsPage({ scenario, notify, autoRunToken = 0 }: { scenario: Scenario; notify: Notify; autoRunToken?: number }) {
  const [report, setReport] = useState<ExperimentReport | null>(null)
  const [busy, setBusy] = useState(false)

  async function run() {
    setBusy(true)
    try { setReport(await api.experiments()); notify('Experiments completed from the current backend scenario.', 'success') }
    catch (error) { notify((error as Error).message, 'error') }
    finally { setBusy(false) }
  }

  useEffect(() => { setReport(null) }, [scenario.id, scenario.capabilities])
  useEffect(() => { if (autoRunToken > 0) void run() }, [autoRunToken])
  const experiments = Object.fromEntries((report?.experiments ?? []).map((item) => [item.id, item.results]))
  const compatibility = experiments.compatibility
  const alternative = experiments.alternative_implementations?.functional_similarity as Record<string, number | { similarity: number }> | undefined
  const operational = experiments.operational_properties
  const relevance = experiments.goal_relevance?.capabilities as Array<Record<string, any>> | undefined
  const relevanceChart = relevance?.map((item) => ({ name: shortName(item.capability_id), coverage: item.goal_effect_coverage * 100 }))

  return <>
    <PageHeading eyebrow="EVALUATE / EXPERIMENTS" title="Experiment results" description="Run the assignment scenarios against the active backend dataset and inspect their numerical outputs." action={<button className="button button-primary" onClick={run} disabled={busy}>{busy ? <RefreshCw className="spin" size={15} /> : <FlaskConical size={15} />}{busy ? 'Running…' : 'Run all experiments'}</button>} />
    {busy && <Panel><Loading label="The backend is computing experiment metrics…" /></Panel>}
    {!report && !busy && <Panel><EmptyState title="Ready to evaluate" description={`Run the seven experiment groups using “${scenario.name}”. Results are calculated by the backend, not prefilled in the interface.`} /></Panel>}
    {report && <>
      <div className="metric-grid four-cols">
        <MetricCard label="Capabilities evaluated" value={report.metrics.capability_count} hint="Across the active scenario" icon={Activity} />
        <MetricCard label="State snapshots" value={report.metrics.state_count} hint="Formal state records" />
        <MetricCard label="Feature dimensions" value={report.metrics.embedding_dimensions_observed} hint="Observed across atomic vectors" />
        <MetricCard label="Experiment groups" value={report.experiments.length} hint="Computed on this run" icon={CheckCircle2} />
      </div>
      {report.experiments.some((item) => item.skipped) && <div className="experiment-skip-list" aria-label="Experiments skipped for this scenario">{report.experiments.filter((item) => item.skipped).map((item) => <div key={item.id}><strong>{title(item.id.replaceAll('_', ' '))}</strong><span>Skipped: {item.skipped}</span></div>)}</div>}
      <div className="experiment-grid">
        <Panel className="experiment-card"><ExperimentHeading number="01" title="Directional compatibility" subtitle="Effects and typed outputs must supply next-stage requirements." />
          {compatibility && <div className="compat-experiment-pairs">{compatibility.compatible_pair && <CompatibilityPair label={`${shortName(compatibility.compatible_pair.producer_id)} → ${shortName(compatibility.compatible_pair.consumer_id)}`} result={compatibility.compatible_pair} />}{compatibility.incompatible_pair && <CompatibilityPair label={`${shortName(compatibility.incompatible_pair.producer_id)} → ${shortName(compatibility.incompatible_pair.consumer_id)}`} result={compatibility.incompatible_pair} />}</div>}
        </Panel>
        <Panel className="experiment-card"><ExperimentHeading number="02" title="Alternative implementations" subtitle="Shared formal function, different execution mechanisms." />
          {alternative && <><div className="similarity-bars">{Object.entries(alternative).map(([pair, raw]) => { const score = typeof raw === 'number' ? raw : raw.similarity; return <div className="similarity-bar-row" key={pair}><span>{title(pair.replaceAll('_', ' / '))}</span><div className="score-track"><i style={{ width: `${score * 100}%` }} /></div><strong>{score.toFixed(3)}</strong></div> })}</div><div className="chart-note">The backend reports weighted section cosine. Similarity does not mean the capabilities compose.</div></>}
        </Panel>
        <Panel className="experiment-card"><ExperimentHeading number="03" title="Goal relevance" subtitle="Exact effect overlap shows whether a capability contributes to the checkout goal." />
          {relevanceChart && <div className="chart-box"><ResponsiveContainer width="100%" height={208}><BarChart data={relevanceChart} margin={{ top: 10, right: 8, bottom: 16, left: -14 }}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e9edf2" /><XAxis dataKey="name" tick={{ fontSize: 10, fill: '#788493' }} interval={0} angle={-18} textAnchor="end" /><YAxis domain={[0, 40]} tick={{ fontSize: 10, fill: '#788493' }} unit="%" /><Tooltip formatter={(value) => [`${Number(value).toFixed(1)}%`, 'Goal coverage']} /><Bar dataKey="coverage" fill="#286fba" radius={[4, 4, 0, 0]} maxBarSize={34} /></BarChart></ResponsiveContainer></div>}
          {relevance && <div className="result-chip-row"><Pill tone="green">{relevance.filter((item) => item.relevant).length} relevant</Pill><Pill tone="neutral">{relevance.filter((item) => !item.relevant).length} unrelated</Pill></div>}
        </Panel>
        <Panel className="experiment-card"><ExperimentHeading number="04" title="Operational properties" subtitle="Compare execution cost, reliability, and availability on implementations." />
          {operational && <><div className="implementation-chart"><div className="chart-caption">Execution time (ms)</div>{operational.implementations.map((item: Record<string, any>) => <div className="operational-row" key={item.capability_id}><span>{shortName(item.capability_id)}</span><div className="time-track"><i style={{ width: `${Math.max(4, item.cost_time_ms / Math.max(...operational.implementations.map((x: Record<string, number>) => x.cost_time_ms)) * 100)}%` }} /></div><strong>{item.cost_time_ms}</strong></div>)}</div><div className="ops-table"><div><span>Implementation</span><span>Reliability</span><span>Availability</span></div>{operational.implementations.map((item: Record<string, any>) => <div key={item.capability_id}><strong>{shortName(item.capability_id)}</strong><span>{(item.reliability * 100).toFixed(1)}%</span><span>{(item.availability * 100).toFixed(1)}%</span></div>)}</div><div className="composite-operational"><strong>Three-stage chain</strong><span>{operational.chain_cost.time_ms} ms</span><span>Rel. {(operational.chain_reliability * 100).toFixed(2)}%</span><span>Avail. {(operational.chain_availability * 100).toFixed(2)}%</span></div></>}
        </Panel>
        <Panel className="experiment-card"><ExperimentHeading number="05" title="Three-capability composition" subtitle="A validated chain produces a composite formal capability and vector." />
          {experiments.three_capability_composition && <div className="composition-experiment"><div className="mini-chain">{experiments.three_capability_composition.component_ids.map((id: string, index: number) => <div key={id}><span>{index + 1}</span><strong>{shortName(id)}</strong>{index < 2 && <i>→</i>}</div>)}</div><div className="experiment-output"><span>Composite vector dimensions</span><strong>{Object.keys(experiments.three_capability_composition.embedding).length}</strong></div><div className="experiment-output"><span>Net effects carried forward</span><strong>{experiments.three_capability_composition.composite.effects.length}</strong></div></div>}
        </Panel>
        <Panel className="experiment-card"><ExperimentHeading number="06" title="Formal entity encoding" subtitle="Inspect measured state and goal feature dimensions." />
          {experiments.state_and_goal_encoding && <div className="encoding-counts"><div><span>State dimensions</span><strong>{Object.keys(experiments.state_and_goal_encoding.encoded_state).length}</strong></div><div><span>Goal dimensions</span><strong>{Object.keys(experiments.state_and_goal_encoding.encoded_goal).length}</strong></div><div><span>Initial state already meets goal</span><Pill tone={experiments.state_and_goal_encoding.initial_state_satisfies_goal ? 'green' : 'amber'}>{experiments.state_and_goal_encoding.initial_state_satisfies_goal ? 'Yes' : 'No'}</Pill></div></div>}
        </Panel>
        <Panel className="experiment-card"><ExperimentHeading number="07" title="State awareness" subtitle="A formal capability is checked against the initial state’s predicates." />
          {experiments.state_awareness && <div className="state-awareness-result"><div><span className={`result-indicator ${experiments.state_awareness.applicable ? 'pass' : 'fail'}`} /><strong>{experiments.state_awareness.applicable ? 'Applicable' : 'Not applicable'}</strong></div>{experiments.state_awareness.precondition_constraint_evidence.map((item: Record<string, any>, index: number) => <div className="evidence-row" key={index}><code>{item.predicate.name} {item.predicate.operator} {JSON.stringify(item.predicate.value)}</code><Pill tone={item.satisfied ? 'green' : 'red'}>{item.satisfied ? 'true' : 'false'}</Pill></div>)}</div>}
        </Panel>
      </div>
      <Panel className="full-results"><div className="panel-heading"><span className="panel-icon"><AlertTriangle size={17} /></span><div><h3>Run context</h3><p>Results came from the current scenario loaded in the API process.</p></div><Pill tone="blue">{report.scenario_id}</Pill></div><div className="run-context-note">Experiment outputs can change when you update capability definitions or operational values in Scenario editor and save the scenario to the backend.</div></Panel>
    </>}
  </>
}

function ExperimentHeading({ number, title, subtitle }: { number: string; title: string; subtitle: string }) {
  return <div className="experiment-heading"><span>{number}</span><div><h3>{title}</h3><p>{subtitle}</p></div></div>
}

function CompatibilityPair({ label, result }: { label: string; result: Record<string, any> }) {
  return <div className="compat-pair"><div><strong>{label}</strong><Pill tone={result.compatible ? 'green' : 'red'}>{result.compatible ? 'compatible' : 'incompatible'}</Pill></div>
    {result.evidence.map((item: Record<string, any>, index: number) => <small key={index} className={item.satisfied ? 'evidence-pass' : 'evidence-fail'}>{item.satisfied ? '✓' : '×'} {item.requirement}: {item.name}</small>)}
    {result.reasons?.map((reason: string) => <small className="evidence-fail" key={reason}>{reason}</small>)}
  </div>
}

function shortName(value: string): string { return value.replace(/^create-order-/, '').replaceAll('-', ' ') }
