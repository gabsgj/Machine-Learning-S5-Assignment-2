import { useEffect, useState } from 'react'
import { ArrowRight, GitCompareArrows, ShieldQuestion, Target } from 'lucide-react'
import { api } from '../services/api'
import type { Capability, Scenario } from '../types'
import type { Notify } from './types'
import { PageHeading, Panel, Pill, SelectField } from '../components/Primitives'

export function RelationshipsPage({ scenario, notify }: { scenario: Scenario; notify: Notify }) {
  const [producerId, setProducerId] = useState(scenario.capabilities[0]?.id ?? '')
  const [consumerId, setConsumerId] = useState(scenario.capabilities[1]?.id ?? '')
  const [similarity, setSimilarity] = useState<{ similarity: number; metric: string; section_scores: Record<string, { similarity: number; weight: number }> } | null>(null)
  const [compatibility, setCompatibility] = useState<Awaited<ReturnType<typeof api.compatibility>> | null>(null)
  const [busy, setBusy] = useState(false)
  const [relevanceCapability, setRelevanceCapability] = useState(scenario.capabilities[0]?.id ?? '')
  const [goalId, setGoalId] = useState(scenario.goals[0]?.id ?? '')
  const [relevance, setRelevance] = useState<Awaited<ReturnType<typeof api.goalRelevance>> | null>(null)
  const [stateId, setStateId] = useState(scenario.states[0]?.id ?? '')
  const [stateGoal, setStateGoal] = useState<Awaited<ReturnType<typeof api.stateGoal>> | null>(null)
  const producer = scenario.capabilities.find((item) => item.id === producerId)
  const consumer = scenario.capabilities.find((item) => item.id === consumerId)
  const relCap = scenario.capabilities.find((item) => item.id === relevanceCapability)
  const goal = scenario.goals.find((item) => item.id === goalId)
  const state = scenario.states.find((item) => item.id === stateId)

  useEffect(() => {
    setProducerId(scenario.capabilities[0]?.id ?? ''); setConsumerId(scenario.capabilities[1]?.id ?? '')
    setRelevanceCapability(scenario.capabilities[0]?.id ?? ''); setGoalId(scenario.goals[0]?.id ?? '')
    setStateId(scenario.states[0]?.id ?? ''); setSimilarity(null); setCompatibility(null); setRelevance(null); setStateGoal(null)
  }, [scenario.id, scenario.capabilities, scenario.goals, scenario.states])

  async function comparePair() {
    if (!producer || !consumer) return
    setBusy(true); setCompatibility(null); setSimilarity(null)
    try {
      const [similarityResult, compatibilityResult] = await Promise.all([api.compareCapabilities(producer, consumer), api.compatibility(producer, consumer)])
      setSimilarity(similarityResult); setCompatibility(compatibilityResult)
    } catch (error) { notify((error as Error).message, 'error') }
    finally { setBusy(false) }
  }

  async function analyzeGoal() {
    if (!relCap || !goal) return
    setBusy(true)
    try { setRelevance(await api.goalRelevance(relCap, goal)) }
    catch (error) { notify((error as Error).message, 'error') }
    finally { setBusy(false) }
  }

  async function testGoal() {
    if (!state || !goal) return
    setBusy(true)
    try { setStateGoal(await api.stateGoal(state, goal)) }
    catch (error) { notify((error as Error).message, 'error') }
    finally { setBusy(false) }
  }

  return <>
    <PageHeading eyebrow="EXPLORE / RELATIONSHIPS" title="Similarity is not compatibility" description="Compare representation resemblance separately from the directional checks required to compose two capabilities." />
    <Panel className="relationship-panel">
      <div className="panel-heading relationship-title"><span className="panel-icon"><GitCompareArrows size={17} /></span><div><h3>Capability pair analysis</h3><p>Similarity compares vector sections; compatibility checks actual typed and state dependencies.</p></div></div>
      <div className="pair-selectors">
        <SelectField label="Producer · runs first" value={producerId} onChange={(value) => { setProducerId(value); setSimilarity(null); setCompatibility(null) }}>
          {scenario.capabilities.map((item) => <option value={item.id} key={item.id}>{item.name} · {item.type}</option>)}
        </SelectField>
        <div className="flow-arrow"><ArrowRight size={19} /></div>
        <SelectField label="Consumer · runs next" value={consumerId} onChange={(value) => { setConsumerId(value); setSimilarity(null); setCompatibility(null) }}>
          {scenario.capabilities.map((item) => <option value={item.id} key={item.id}>{item.name} · {item.type}</option>)}
        </SelectField>
        <button className="button button-primary analyze-button" disabled={busy || !producer || !consumer} onClick={comparePair}>{busy ? 'Analyzing…' : 'Analyze pair'}</button>
      </div>
      {producer && consumer && <div className="pair-signatures"><Signature capability={producer} /><div className="signature-link"><ArrowRight size={17} /><span>candidate handoff</span></div><Signature capability={consumer} /></div>}
      {(similarity || compatibility) && <div className="analysis-results">
        <div className="similarity-result"><div className="result-heading"><div><span className="eyebrow">VECTOR RESEMBLANCE</span><h3>{similarity?.similarity.toFixed(3) ?? '—'}</h3><p>{similarity?.metric}</p></div><div className="similarity-dial" style={{ '--score': `${(similarity?.similarity ?? 0) * 100}%` } as React.CSSProperties}><span>{((similarity?.similarity ?? 0) * 100).toFixed(0)}<small>%</small></span></div></div>
          {similarity && <div className="section-scores">{Object.entries(similarity.section_scores).sort(([, a], [, b]) => b.weight - a.weight).map(([key, row]) => <div className="section-score" key={key}><span>{key}</span><div className="score-track"><i style={{ width: `${row.similarity * 100}%` }} /></div><strong>{row.similarity.toFixed(2)}</strong></div>)}</div>}
        </div>
        <div className={`compatibility-result ${compatibility?.compatible ? 'is-compatible' : 'is-incompatible'}`}>
          <div className="result-heading"><div><span className="eyebrow">DIRECTIONAL COMPOSABILITY</span><h3>{compatibility?.compatible ? 'Compatible' : 'Incompatible'}</h3><p>Producer output/effect → consumer input/precondition</p></div><Pill tone={compatibility?.compatible ? 'green' : 'red'}>{compatibility?.compatible ? 'Link valid' : 'Link blocked'}</Pill></div>
          <div className="compat-evidence">{compatibility?.evidence.map((row, index) => <div className="evidence-row" key={index}><div><strong>{String(row.requirement)}</strong><small>{String(row.name)}</small></div><Pill tone={row.satisfied ? 'green' : 'red'}>{row.satisfied ? 'satisfied' : 'not satisfied'}</Pill></div>)}</div>
          {!!compatibility?.reasons.length && <div className="reason-list">{compatibility.reasons.map((reason) => <div key={reason}>• {reason}</div>)}</div>}
        </div>
      </div>}
      {!similarity && !compatibility && <div className="relationship-explainer"><div><span className="explain-dot resemblance" /><strong>Similar</strong><small>Formal features resemble each other</small></div><span className="not-equal">≠</span><div><span className="explain-dot compatible" /><strong>Composable</strong><small>Handoff requirements are satisfied</small></div></div>}
    </Panel>

    <div className="relationship-lower-grid">
      <Panel><div className="panel-heading"><span className="panel-icon goal-icon"><Target size={17} /></span><div><h3>Goal relevance</h3><p>Measure effect overlap with a desired outcome</p></div></div>
        <SelectField label="Capability" value={relevanceCapability} onChange={(value) => { setRelevanceCapability(value); setRelevance(null) }}>{scenario.capabilities.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</SelectField>
        <SelectField label="Goal" value={goalId} onChange={(value) => { setGoalId(value); setRelevance(null); setStateGoal(null) }}>{scenario.goals.map((item) => <option value={item.id} key={item.id}>{item.id}</option>)}</SelectField>
        <button className="button button-secondary full-button" onClick={analyzeGoal} disabled={busy || !relCap || !goal}>Analyze effect relevance</button>
        {relevance && <div className="relevance-result"><div className="relevance-top"><Pill tone={relevance.relevant ? 'green' : 'amber'}>{relevance.relevant ? 'Contributes to goal' : 'No matching effects'}</Pill><strong>{(relevance.goal_effect_coverage * 100).toFixed(0)}% coverage</strong></div><div className="score-track wide"><i style={{ width: `${relevance.goal_effect_coverage * 100}%` }} /></div><div className="matched-list"><span>Matching goal variables</span><div>{relevance.matched_goal_variables.length ? relevance.matched_goal_variables.map((item) => <code key={item}>{item}</code>) : <small>None</small>}</div></div><div className="similarity-caption">Effect-space cosine <strong>{relevance.goal_effect_similarity.toFixed(3)}</strong></div></div>}
      </Panel>
      <Panel><div className="panel-heading"><span className="panel-icon"><ShieldQuestion size={17} /></span><div><h3>State satisfies goal?</h3><p>Evaluate the desired conditions against one state snapshot</p></div></div>
        <SelectField label="Application state" value={stateId} onChange={(value) => { setStateId(value); setStateGoal(null) }}>{scenario.states.map((item) => <option value={item.id} key={item.id}>{item.id}</option>)}</SelectField>
        <button className="button button-secondary full-button" onClick={testGoal} disabled={busy || !state || !goal}>Evaluate state against goal</button>
        {stateGoal && <div className="check-result"><div className="check-result-title"><span className={`result-indicator ${stateGoal.satisfied ? 'pass' : 'fail'}`} />{stateGoal.satisfied ? 'Goal conditions are met' : 'Goal conditions are not met'}</div>{stateGoal.evidence.map((row, index) => <div className="evidence-row" key={index}><code>{String(row.condition.name)} {String(row.condition.operator)} {JSON.stringify(row.condition.value)}</code><Pill tone={row.satisfied ? 'green' : 'red'}>{row.satisfied ? 'met' : 'not met'}</Pill></div>)}</div>}
      </Panel>
    </div>
  </>
}

function Signature({ capability }: { capability: Capability }) {
  return <div className="signature-card"><div className="signature-name"><strong>{capability.name}</strong><Pill tone="blue">{capability.type}</Pill></div>
    <div className="signature-row"><span>Outputs / effects</span><div>{capability.outputs.map((item) => <code key={item.name}>{item.name}:{item.type}</code>)}{capability.effects.map((item, index) => <code key={`${item.name}-${index}`}>{item.name}={String(item.value)}</code>)}</div></div>
    <div className="signature-row"><span>Next requires</span><div>{capability.inputs.filter((item) => item.required).map((item) => <code key={item.name}>{item.name}:{item.type}</code>)}{capability.preconditions.map((item, index) => <code key={`${item.name}-${index}`}>{item.name}{item.operator}{String(item.value)}</code>)}</div></div>
  </div>
}
