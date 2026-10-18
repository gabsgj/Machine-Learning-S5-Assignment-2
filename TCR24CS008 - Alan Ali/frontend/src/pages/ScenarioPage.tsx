import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { Braces, Download, FileJson2, RotateCcw, Upload } from 'lucide-react'
import type { Capability, Goal, Predicate, Scenario, State } from '../types'
import { api } from '../services/api'
import { Notice, PageHeading, Panel, Pill } from '../components/Primitives'
import type { Notify } from './types'
import level1SingleCapability from '../../../data/scenarios/examples/level-1-single-capability.json'
import level2CompatiblePair from '../../../data/scenarios/examples/level-2-compatible-pair.json'
import level3FullChain from '../../../data/scenarios/examples/level-3-full-chain.json'
import level4Branching from '../../../data/scenarios/examples/level-4-branching.json'
import level5Everything from '../../../data/scenarios/examples/level-5-everything.json'

type Props = { scenario: Scenario; onScenario: (scenario: Scenario) => void; notify: Notify; onLoadExample: (scenario: Scenario, name: string) => Promise<void>; loadedExample: string | null }
const blankCapability = (): Capability => ({ id: '', name: '', type: 'API', mechanism: {}, inputs: [], outputs: [], preconditions: [], effects: [], constraints: [], resources: [], cost: { time_ms: 0, money: 0, resource: 0, risk: 0, energy: 0 }, reliability: 1, availability: 1, components: [] })
const blankState = (): State => ({ id: '', values: {} })
const blankGoal = (): Goal => ({ id: '', conditions: [] })

export function ScenarioPage({ scenario, onScenario, notify, onLoadExample, loadedExample }: Props) {
  const [activeTab, setActiveTab] = useState<'examples' | 'custom'>('examples')
  const [draft, setDraft] = useState<Scenario>(scenario)
  const [advanced, setAdvanced] = useState(false)
  const [json, setJson] = useState(JSON.stringify(scenario, null, 2))
  const [busy, setBusy] = useState(false)
  const [validation, setValidation] = useState<string | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)
  const [stateId, setStateId] = useState(scenario.states[0]?.id ?? '')
  const [capabilityId, setCapabilityId] = useState(scenario.capabilities[0]?.id ?? '')
  const [producerId, setProducerId] = useState(scenario.capabilities[0]?.id ?? '')
  const [consumerId, setConsumerId] = useState(scenario.capabilities[1]?.id ?? '')
  const [applicability, setApplicability] = useState<Awaited<ReturnType<typeof api.applicability>> | null>(null)
  const [compatibility, setCompatibility] = useState<Awaited<ReturnType<typeof api.compatibility>> | null>(null)

  useEffect(() => { setDraft(scenario); setJson(JSON.stringify(scenario, null, 2)); setValidation(null); setStateId(scenario.states[0]?.id ?? ''); setCapabilityId(scenario.capabilities[0]?.id ?? ''); setProducerId(scenario.capabilities[0]?.id ?? ''); setConsumerId(scenario.capabilities[1]?.id ?? '') }, [scenario])
  const selectedState = draft.states.find((item) => item.id === stateId)
  const selectedCapability = draft.capabilities.find((item) => item.id === capabilityId)
  const producer = draft.capabilities.find((item) => item.id === producerId)
  const consumer = draft.capabilities.find((item) => item.id === consumerId)
  const serializedDraft = useMemo(() => JSON.stringify(draft, null, 2), [draft])
  const variableSuggestions = useMemo(() => scenarioVariableNames(draft), [draft])
  const valueSuggestions = useMemo(() => scenarioValuesByVariable(draft), [draft])
  const valuesForVariable = (name: string) => valueSuggestions.get(name) ?? []
  useEffect(() => { if (!advanced) setJson(serializedDraft) }, [serializedDraft, advanced])

  function updateDraft(next: Scenario) { setDraft(next); setValidation(null) }
  async function save() {
    setBusy(true); setValidation(null)
    try {
      const value = advanced ? JSON.parse(json) as unknown as Scenario : draft
      validateScenario(value)
      const saved = await api.saveScenario(value)
      onScenario(saved); setDraft(saved); setJson(JSON.stringify(saved, null, 2)); notify('Scenario validated and saved to the backend.', 'success')
    } catch (error) { const message = (error as Error).message; setValidation(message); notify(message, 'error') }
    finally { setBusy(false) }
  }
  async function reload() {
    setBusy(true); setValidation(null)
    try { const current = await api.getScenario(); onScenario(current); setDraft(current); setJson(JSON.stringify(current, null, 2)); notify('Loaded the active scenario from the backend.', 'success') }
    catch (error) { notify((error as Error).message, 'error') } finally { setBusy(false) }
  }
  async function readFile(file?: File) {
    if (!file) return
    try { const text = await file.text(); const parsed = JSON.parse(text) as unknown as Scenario; validateScenario(parsed); setDraft(parsed); setJson(JSON.stringify(parsed, null, 2)); setAdvanced(false); notify(`Imported ${file.name} into the form. Save to validate it with the API.`, 'info') }
    catch (error) { setValidation((error as Error).message || 'Could not read the selected JSON file.') }
  }
  function download() {
    const text = advanced ? json : serializedDraft
    const blob = new Blob([text], { type: 'application/json' }); const url = URL.createObjectURL(blob); const anchor = document.createElement('a')
    anchor.href = url; anchor.download = `${draft.id || 'scenario'}.json`; anchor.click(); URL.revokeObjectURL(url)
  }

  async function checkApplicability() {
    if (!selectedState || !selectedCapability) return
    try { setApplicability(await api.applicability(selectedState, selectedCapability)) }
    catch (error) { notify((error as Error).message, 'error') }
  }
  async function checkCompatibility() {
    if (!producer || !consumer) return
    try { setCompatibility(await api.compatibility(producer, consumer)) }
    catch (error) { notify((error as Error).message, 'error') }
  }

  return <>
    <PageHeading eyebrow="WORKSPACE / SCENARIO" title="Scenario editor" description="Edit the active scenario’s states, goals, and capabilities with structured fields. Save validates the complete scenario with the backend." action={<Pill tone="blue">Single active scenario</Pill>} />
    <div className="scenario-tabs" role="tablist" aria-label="Scenario editor sections">
      <button role="tab" aria-selected={activeTab === 'examples'} className={activeTab === 'examples' ? 'active' : ''} onClick={() => setActiveTab('examples')}>Example Scenarios</button>
      <button role="tab" aria-selected={activeTab === 'custom'} className={activeTab === 'custom' ? 'active' : ''} onClick={() => setActiveTab('custom')}>Custom Scenario</button>
    </div>
    {activeTab === 'examples' ? <ExampleScenarios onLoad={onLoadExample} /> : <>
    {loadedExample && <div className="notice notice-info loaded-example-note">Loaded from: {loadedExample} example â€” edits apply to your working scenario, not the example file.</div>}
    <div className="scenario-summary-grid"><div><span>Scenario ID</span><strong>{draft.id}</strong></div><div><span>States</span><strong>{draft.states.length}</strong></div><div><span>Goals</span><strong>{draft.goals.length}</strong></div><div><span>Capabilities</span><strong>{draft.capabilities.length}</strong></div></div>
    <Panel className="scenario-editor-panel">
      <div className="panel-heading"><span className="panel-icon"><FileJson2 size={17} /></span><div><h3>Scenario data</h3><p>All sections save together to the one scenario held by the backend.</p></div><div className="editor-actions push-right"><button className="button button-quiet" onClick={reload} disabled={busy}><RotateCcw size={14} />Reload backend</button><button className="button button-quiet" onClick={() => fileInput.current?.click()}><Upload size={14} />Import JSON</button><input ref={fileInput} type="file" accept="application/json,.json" hidden onChange={(event) => { void readFile(event.target.files?.[0]); event.currentTarget.value = '' }} /><button className="button button-quiet" onClick={download}><Download size={14} />Download</button></div></div>
      <div className="scenario-form-section"><h3>Scenario details</h3><div className="scenario-fields"><TextField label="Scenario ID" value={draft.id} onChange={(id) => updateDraft({ ...draft, id })} /><TextField label="Scenario name" value={draft.name} onChange={(name) => updateDraft({ ...draft, name })} /></div></div>
      <StateForm states={draft.states} onChange={(states) => updateDraft({ ...draft, states })} variableSuggestions={variableSuggestions} valuesForVariable={valuesForVariable} />
      <GoalForm goals={draft.goals} onChange={(goals) => updateDraft({ ...draft, goals })} variableSuggestions={variableSuggestions} valuesForVariable={valuesForVariable} />
      <CapabilityForm capabilities={draft.capabilities} onChange={(capabilities) => updateDraft({ ...draft, capabilities })} variableSuggestions={variableSuggestions} valuesForVariable={valuesForVariable} resourceSuggestions={scenarioResourceSuggestions(draft)} mechanismKeySuggestions={(capabilityId) => scenarioMechanismKeySuggestions(draft, capabilityId)} />
      <div className="advanced-json-toggle"><button className="text-button" onClick={() => { setAdvanced((current) => !current); setValidation(null) }}><Braces size={14} />{advanced ? 'Hide advanced JSON' : 'Advanced JSON editor'}</button><span>For direct editing of fields beyond the structured controls</span></div>
      {advanced && <><div className="editor-toolbar"><span><i className="editor-dot" />JSON Â· UTF-8</span><span>Backend schema: Scenario</span></div><textarea className="scenario-editor" spellCheck={false} value={json} onChange={(event) => { setJson(event.target.value); setValidation(null) }} aria-label="Advanced scenario JSON editor" /></>}
      {validation && <div className="validation-output"><Notice tone="error">{validation}</Notice></div>}
      <div className="editor-footer"><div className="editor-hint">Backend validation checks required fields, types, ranges, and formal model constraints.</div><button className="button button-primary" onClick={save} disabled={busy}>{busy ? 'Savingâ€¦' : 'Validate & save scenario'}</button></div>
    </Panel>
    <div className="scenario-hints-grid">
      <Panel><div className="panel-heading"><span className="panel-icon"><Braces size={17} /></span><div><h3>Applicability hint</h3><p>Backend checks selected state values against capability preconditions.</p></div></div>
        <div className="scenario-fields"><Select label="State" value={stateId} onChange={(value) => { setStateId(value); setApplicability(null) }} options={draft.states.map((item) => [item.id, item.id])} /><Select label="Capability" value={capabilityId} onChange={(value) => { setCapabilityId(value); setApplicability(null) }} options={draft.capabilities.map((item) => [item.id, item.name])} /></div>
        <button className="button button-secondary full-button" disabled={!selectedState || !selectedCapability} onClick={() => void checkApplicability()}>Check applicability</button>
        {applicability && <div className="hint-result"><strong>{applicability.applicable ? 'Applicable in the selected state' : 'Not applicable in the selected state'}</strong>{applicability.evidence.map((row, index) => <div className="evidence-row" key={index}><code>{formatPredicate(row.predicate)}</code><Pill tone={row.satisfied ? 'green' : 'red'}>{row.satisfied ? 'satisfied' : 'not satisfied'}</Pill></div>)}{!applicability.evidence.length && <small>No preconditions were declared.</small>}</div>}
      </Panel>
      <Panel><div className="panel-heading"><span className="panel-icon"><Braces size={17} /></span><div><h3>Composition compatibility hint</h3><p>Pass full capability objects to the backend compatibility check.</p></div></div>
        <div className="scenario-fields"><Select label="Producer" value={producerId} onChange={(value) => { setProducerId(value); setCompatibility(null) }} options={draft.capabilities.map((item) => [item.id, item.name])} /><Select label="Consumer" value={consumerId} onChange={(value) => { setConsumerId(value); setCompatibility(null) }} options={draft.capabilities.map((item) => [item.id, item.name])} /></div>
        <button className="button button-secondary full-button" disabled={!producer || !consumer} onClick={() => void checkCompatibility()}>Check compatibility</button>
        {compatibility && <div className="hint-result"><strong>{compatibility.compatible ? 'Capabilities are compatible' : 'Capabilities are incompatible'}</strong>{compatibility.reasons.map((reason, index) => <p key={index}>{reason}</p>)}{compatibility.evidence.map((row, index) => <div className="evidence-row" key={index}><code>{String(row.kind ?? row.requirement ?? row.field ?? 'evidence')}</code><Pill tone={row.satisfied ? 'green' : 'red'}>{row.satisfied ? 'satisfied' : 'missing'}</Pill></div>)}</div>}
      </Panel>
    </div>
    </>}
  </>
}

function ExampleScenarios({ onLoad }: { onLoad: Props['onLoadExample'] }) {
  const examples: Array<{ name: string; description: string; scenario: Scenario; advanced?: boolean }> = [
    { name: 'Level 1 · Single capability, single state', description: 'Baseline: load one state and check its one applicable capability.', scenario: level1SingleCapability as unknown as Scenario },
    { name: 'Level 2 · Compatible pair', description: 'Switch states to see payment become applicable after order creation.', scenario: level2CompatiblePair as unknown as Scenario },
    { name: 'Level 3 · Full chain', description: 'Step through a three capability chain and check the final goal.', scenario: level3FullChain as unknown as Scenario },
    { name: 'Level 4 · Branching', description: 'See two valid next capabilities available from one state.', scenario: level4Branching as unknown as Scenario },
    { name: 'Level 5 · Everything', description: 'Explore a full chain, alternate implementations, and an irrelevant capability.', scenario: level5Everything as unknown as Scenario, advanced: true },
  ]
  return <section className="example-library"><p className="example-intro">Load a focused, read-only scenario and run its available experiments. You can edit the loaded copy under Custom Scenario.</p><div className="example-card-grid">
    {examples.map((example) => <Panel className="example-card" key={example.scenario.id}><div className="example-card-copy"><span className="eyebrow">{example.advanced ? 'ADVANCED EXAMPLE' : 'EXAMPLE SCENARIO'}</span><h3>{example.name}</h3><p>{example.description}</p></div><button className="button button-primary" onClick={() => void onLoad(example.scenario, example.name)}>Load &amp; Run</button></Panel>)}
  </div></section>
}

type SuggestionProps = { variableSuggestions: string[]; valuesForVariable: (name: string) => string[] }

function StateForm({ states, onChange, variableSuggestions, valuesForVariable }: { states: State[]; onChange: (states: State[]) => void } & SuggestionProps) {
  return <section className="scenario-form-section"><header className="scenario-section-heading"><div><h3>States</h3><p>Named state variables and their current values</p></div><button className="button button-secondary" onClick={() => onChange([...states, blankState()])}>Add state</button></header>
    {states.map((state, index) => <div className="scenario-item" key={`state-${index}`}><div className="scenario-fields"><TextField label="State ID" value={state.id} onChange={(id) => replaceAt(states, index, { ...state, id }, onChange)} /><KeyValueEditor label="Values" value={state.values} keySuggestions={variableSuggestions} valueSuggestionsForKey={valuesForVariable} smartValues onChange={(values) => replaceAt(states, index, { ...state, values }, onChange)} /></div><RemoveButton onClick={() => onChange(states.filter((_, i) => i !== index))} /></div>)}{!states.length && <p className="scenario-empty">No states yet. Add one to describe an application situation.</p>}
  </section>
}

function GoalForm({ goals, onChange, variableSuggestions, valuesForVariable }: { goals: Goal[]; onChange: (goals: Goal[]) => void } & SuggestionProps) {
  return <section className="scenario-form-section"><header className="scenario-section-heading"><div><h3>Goals</h3><p>Each goal is a list of formal conditions.</p></div><button className="button button-secondary" onClick={() => onChange([...goals, blankGoal()])}>Add goal</button></header>
    {goals.map((goal, index) => <div className="scenario-item" key={`goal-${index}`}><TextField label="Goal ID" value={goal.id} onChange={(id) => replaceAt(goals, index, { ...goal, id }, onChange)} /><PredicateList label="Conditions" rows={goal.conditions} onChange={(conditions) => replaceAt(goals, index, { ...goal, conditions }, onChange)} allowEmpty={false} variableSuggestions={variableSuggestions} valuesForVariable={valuesForVariable} /><RemoveButton onClick={() => onChange(goals.filter((_, i) => i !== index))} /></div>)}{!goals.length && <p className="scenario-empty">No goals yet. Add the conditions the application should meet.</p>}
  </section>
}

function CapabilityForm({ capabilities, onChange, variableSuggestions, valuesForVariable, resourceSuggestions, mechanismKeySuggestions }: { capabilities: Capability[]; onChange: (capabilities: Capability[]) => void } & SuggestionProps & { resourceSuggestions: string[]; mechanismKeySuggestions: (capabilityId: string) => string[] }) {
  const types = ['API', 'DATABASE', 'GUI', 'EVENT', 'FUNCTION', 'FILE', 'COMPUTATION', 'MESSAGE', 'SERVICE', 'COMPOSITE']
  return <section className="scenario-form-section"><header className="scenario-section-heading"><div><h3>Capabilities</h3><p>Interfaces, formal conditions, operational cost, and quality values</p></div><button className="button button-secondary" onClick={() => onChange([...capabilities, blankCapability()])}>Add capability</button></header>
    {capabilities.map((capability, index) => <details className="scenario-item capability-form-item" key={`cap-${index}`} open><summary><strong>{capability.name || 'New capability'}</strong><span>{capability.id || 'id required'}</span><RemoveButton onClick={(event) => { event.stopPropagation(); onChange(capabilities.filter((_, i) => i !== index)) }} /></summary>
      <div className="scenario-fields capability-fields"><TextField label="Capability ID" value={capability.id} onChange={(id) => replaceAt(capabilities, index, { ...capability, id }, onChange)} /><TextField label="Name" value={capability.name} onChange={(name) => replaceAt(capabilities, index, { ...capability, name }, onChange)} /><Select label="Type" value={capability.type} onChange={(type) => replaceAt(capabilities, index, { ...capability, type }, onChange)} options={types.map((type) => [type, type])} /><KeyValueEditor label="Mechanism (string values)" value={capability.mechanism} keySuggestions={mechanismKeySuggestions(capability.id)} stringValues onChange={(mechanism) => replaceAt(capabilities, index, { ...capability, mechanism }, onChange)} /></div>
      <IOList label="Inputs" rows={capability.inputs} onChange={(inputs) => replaceAt(capabilities, index, { ...capability, inputs }, onChange)} /><IOList label="Outputs" rows={capability.outputs} onChange={(outputs) => replaceAt(capabilities, index, { ...capability, outputs }, onChange)} />
      <PredicateList label="Preconditions" rows={capability.preconditions} onChange={(preconditions) => replaceAt(capabilities, index, { ...capability, preconditions }, onChange)} variableSuggestions={variableSuggestions} valuesForVariable={valuesForVariable} /><PredicateList label="Effects" rows={capability.effects} onChange={(effects) => replaceAt(capabilities, index, { ...capability, effects }, onChange)} variableSuggestions={variableSuggestions} valuesForVariable={valuesForVariable} /><PredicateList label="Constraints" rows={capability.constraints} onChange={(constraints) => replaceAt(capabilities, index, { ...capability, constraints }, onChange)} variableSuggestions={variableSuggestions} valuesForVariable={valuesForVariable} />
      <div className="scenario-fields capability-fields"><StringList label="Resources" rows={capability.resources} suggestions={resourceSuggestions} onChange={(resources) => replaceAt(capabilities, index, { ...capability, resources }, onChange)} /><KeyValueEditor label="Cost" value={capability.cost} onChange={(cost) => replaceAt(capabilities, index, { ...capability, cost: { time_ms: 0, money: 0, resource: 0, risk: 0, energy: 0, ...cost } }, onChange)} numeric /><NumberField label="Reliability (0â€“1)" value={capability.reliability} onChange={(reliability) => replaceAt(capabilities, index, { ...capability, reliability }, onChange)} /><NumberField label="Availability (0â€“1)" value={capability.availability} onChange={(availability) => replaceAt(capabilities, index, { ...capability, availability }, onChange)} /><CapabilityIdList rows={capability.components} capabilityIds={capabilities.map((item) => item.id).filter(Boolean)} onChange={(components) => replaceAt(capabilities, index, { ...capability, components }, onChange)} /></div>
    </details>)}{!capabilities.length && <p className="scenario-empty">No capabilities yet. Add a service, function, or other formal operation.</p>}
  </section>
}

function PredicateList({ label, rows, onChange, allowEmpty = true, variableSuggestions = [], valuesForVariable = () => [] }: { label: string; rows: Predicate[]; onChange: (rows: Predicate[]) => void; allowEmpty?: boolean; variableSuggestions?: string[]; valuesForVariable?: (name: string) => string[] }) {
  const operators = ['=', '!=', '>', '>=', '<', '<=', 'in']
  return <div className="scenario-sublist"><div className="scenario-sublist-heading"><strong>{label}</strong><button className="text-button" onClick={() => onChange([...rows, { name: '', operator: '=', value: '' }])}>Add condition</button></div>{rows.map((row, index) => <div className="predicate-row" key={index}><SuggestCombobox label="Variable" value={row.name} onChange={(name) => replaceAt(rows, index, { ...row, name }, onChange)} suggestions={variableSuggestions} /><Select label="Operator" value={row.operator} onChange={(operator) => replaceAt(rows, index, { ...row, operator: operator as Predicate['operator'] }, onChange)} options={operators.map((operator) => [operator, operator])} /><SuggestCombobox label="Value" value={formatSmartValue(row.value)} onChange={(value) => replaceAt(rows, index, { ...row, value: parseSmartValue(value) }, onChange)} suggestions={valuesForVariable(row.name)} /><RemoveButton onClick={() => onChange(rows.filter((_, i) => i !== index))} /></div>)}{!rows.length && !allowEmpty && <p className="scenario-empty">A goal needs at least one condition.</p>}</div>
}

function IOList({ label, rows, onChange }: { label: string; rows: Array<{ name: string; type: string; domain?: string | null; required?: boolean }>; onChange: (rows: Array<{ name: string; type: string; domain?: string | null; required?: boolean }>) => void }) {
  return <div className="scenario-sublist"><div className="scenario-sublist-heading"><strong>{label}</strong><button className="text-button" onClick={() => onChange([...rows, { name: '', type: '', domain: null, required: true }])}>Add field</button></div>{rows.map((row, index) => <div className="predicate-row io-row" key={index}><TextField label="Name" value={row.name} onChange={(name) => replaceAt(rows, index, { ...row, name }, onChange)} /><TextField label="Type" value={row.type} onChange={(type) => replaceAt(rows, index, { ...row, type }, onChange)} /><TextField label="Domain (optional)" value={row.domain ?? ''} onChange={(domain) => replaceAt(rows, index, { ...row, domain: domain || null }, onChange)} /><label className="check-field"><input type="checkbox" checked={row.required ?? true} onChange={(event) => replaceAt(rows, index, { ...row, required: event.target.checked }, onChange)} />Required</label><RemoveButton onClick={() => onChange(rows.filter((_, i) => i !== index))} /></div>)}</div>
}

function StringList({ label, rows, onChange, suggestions = [] }: { label: string; rows: string[]; onChange: (rows: string[]) => void; suggestions?: string[] }) {
  return <div className="scenario-sublist"><div className="scenario-sublist-heading"><strong>{label}</strong><button className="text-button" onClick={() => onChange([...rows, ''])}>Add item</button></div>{rows.map((row, index) => <div className="string-row" key={index}><SuggestCombobox label={label.endsWith('s') ? label.slice(0, -1) : label} value={row} onChange={(value) => replaceAt(rows, index, value, onChange)} suggestions={suggestions} /><RemoveButton onClick={() => onChange(rows.filter((_, i) => i !== index))} /></div>)}</div>
}

function KeyValueEditor({ label, value, onChange, numeric = false, stringValues = false, keySuggestions, valueSuggestionsForKey, smartValues = false }: { label: string; value: Record<string, unknown>; onChange: (value: Record<string, any>) => void; numeric?: boolean; stringValues?: boolean; keySuggestions?: string[]; valueSuggestionsForKey?: (key: string) => string[]; smartValues?: boolean }) {
  const entries = Object.entries(value)
  return <div className="scenario-sublist"><div className="scenario-sublist-heading"><strong>{label}</strong><button className="text-button" onClick={() => onChange({ ...value, '': numeric ? 0 : '' })}>Add field</button></div>{entries.map(([key, item], index) => <div className="key-value-row" key={`${index}-${key}`}>{keySuggestions === undefined ? <TextField label="Name" value={key} onChange={(next) => { const result = { ...value }; delete result[key]; result[next] = item; onChange(result) }} /> : <SuggestCombobox label="Name" value={key} suggestions={keySuggestions} onChange={(next) => { const result = { ...value }; delete result[key]; result[next] = item; onChange(result) }} />}{smartValues ? <SuggestCombobox label="Value" value={formatSmartValue(item)} suggestions={valueSuggestionsForKey?.(key) ?? []} onChange={(next) => onChange({ ...value, [key]: parseSmartValue(next) })} /> : <TextField label={numeric ? 'Number' : stringValues ? 'Value' : 'Value (JSON)'} value={numeric || stringValues ? String(item) : JSON.stringify(item)} onChange={(next) => { let parsed: unknown = next; if (numeric) parsed = Number(next); else if (!stringValues) { try { parsed = JSON.parse(next) as unknown } catch { return } } onChange({ ...value, [key]: parsed }) }} />}<RemoveButton onClick={() => { const result = { ...value }; delete result[key]; onChange(result) }} /></div>)}</div>
}

function SuggestCombobox({ label, value, onChange, suggestions }: { label: string; value: string; onChange: (value: string) => void; suggestions: string[] }) {
  const listId = useId()
  return <label className="field scenario-field"><span>{label}</span><input role="combobox" aria-autocomplete="list" list={listId} value={value} onChange={(event) => onChange(event.target.value)} /><datalist id={listId}>{suggestions.map((option) => <option value={option} key={option} />)}</datalist></label>
}

function CapabilityIdList({ rows, capabilityIds, onChange }: { rows: string[]; capabilityIds: string[]; onChange: (rows: string[]) => void }) {
  return <div className="scenario-sublist"><div className="scenario-sublist-heading"><strong>Components</strong><button className="text-button" onClick={() => onChange([...rows, ''])}>Add component</button></div>{rows.map((row, index) => <div className="string-row" key={index}><Select label="Capability ID" value={row} onChange={(next) => replaceAt(rows, index, next, onChange)} options={capabilityIds.map((id) => [id, id])} /><RemoveButton onClick={() => onChange(rows.filter((_, i) => i !== index))} /></div>)}</div>
}

function TextField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) { return <label className="field scenario-field"><span>{label}</span><input value={value} onChange={(event) => onChange(event.target.value)} /></label> }
function NumberField({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) { return <label className="field scenario-field"><span>{label}</span><input type="number" min="0" max="1" step="0.01" value={value} onChange={(event) => onChange(Number(event.target.value))} /></label> }
function Select({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[][] }) { return <label className="field scenario-field"><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)}>{options.length ? options.map(([optionValue, text]) => <option key={optionValue} value={optionValue}>{text}</option>) : <option value="">No options</option>}</select></label> }
function RemoveButton({ onClick }: { onClick: (event: React.MouseEvent<HTMLButtonElement>) => void }) { return <button type="button" className="remove-item" aria-label="Remove item" onClick={onClick}>Ã—</button> }
function replaceAt<T>(rows: T[], index: number, value: T, onChange: (rows: T[]) => void) { onChange(rows.map((row, i) => i === index ? value : row)) }
function formatPredicate(predicate: Record<string, unknown>) { return `${String(predicate.name)} ${String(predicate.operator)} ${JSON.stringify(predicate.value)}` }
function scenarioVariableNames(scenario: Scenario): string[] {
  const names = new Set<string>()
  scenario.states.forEach((state) => Object.keys(state.values).forEach((name) => { if (name) names.add(name) }))
  scenario.goals.forEach((goal) => goal.conditions.forEach((item) => { if (item.name) names.add(item.name) }))
  scenario.capabilities.forEach((capability) => [...capability.preconditions, ...capability.effects, ...capability.constraints].forEach((item) => { if (item.name) names.add(item.name) }))
  return [...names]
}
function scenarioValuesByVariable(scenario: Scenario): Map<string, string[]> {
  const values = new Map<string, Map<string, string>>()
  const add = (name: string, value: unknown) => {
    if (!name) return
    const encoded = JSON.stringify(value)
    const entries = values.get(name) ?? new Map<string, string>()
    entries.set(encoded, formatSmartValue(value)); values.set(name, entries)
  }
  scenario.states.forEach((state) => Object.entries(state.values).forEach(([name, value]) => add(name, value)))
  scenario.goals.forEach((goal) => goal.conditions.forEach((item) => add(item.name, item.value)))
  scenario.capabilities.forEach((capability) => [...capability.preconditions, ...capability.effects, ...capability.constraints].forEach((item) => add(item.name, item.value)))
  return new Map([...values].map(([name, entries]) => [name, [...entries.values()]]))
}
function scenarioResourceSuggestions(scenario: Scenario): string[] {
  return [...new Set(scenario.capabilities.flatMap((capability) => capability.resources).filter(Boolean))]
}
function scenarioMechanismKeySuggestions(scenario: Scenario, currentCapabilityId: string): string[] {
  return [...new Set(scenario.capabilities.filter((capability) => capability.id !== currentCapabilityId).flatMap((capability) => Object.keys(capability.mechanism)).filter(Boolean))]
}
function formatSmartValue(value: unknown): string {
  if (typeof value !== 'string') return JSON.stringify(value) ?? ''
  return typeof parseSmartValue(value) === 'string' ? value : JSON.stringify(value)
}
function parseSmartValue(value: string): unknown {
  const trimmed = value.trim()
  if (trimmed === 'true') return true
  if (trimmed === 'false') return false
  if (trimmed === 'null') return null
  if (trimmed !== '' && Number.isFinite(Number(trimmed))) return Number(trimmed)
  if (trimmed.startsWith('"') || trimmed.startsWith('[') || trimmed.startsWith('{')) {
    try { return JSON.parse(trimmed) as unknown } catch { /* Treat incomplete JSON as ordinary text while typing. */ }
  }
  return value
}
function validateScenario(value: Scenario) {
  if (!value || typeof value !== 'object') throw new Error('The root value must be a JSON object.')
  if (!value.id?.trim() || !value.name?.trim()) throw new Error('Scenario requires non-empty id and name fields.')
  for (const field of ['states', 'goals', 'capabilities'] as const) if (!Array.isArray(value[field])) throw new Error(`Scenario field â€œ${field}â€ must be an array.`)
}
