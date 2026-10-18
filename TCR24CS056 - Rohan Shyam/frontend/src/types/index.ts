export type Predicate = {
  name: string
  operator: '=' | '!=' | '>' | '>=' | '<' | '<=' | 'in'
  value: unknown
}

export type State = { id: string; values: Record<string, unknown> }
export type Goal = { id: string; conditions: Predicate[] }
export type IOField = { name: string; type: string; domain?: string | null; required?: boolean }
export type Cost = { time_ms: number; money: number; resource: number; risk: number; energy: number }

export type Capability = {
  id: string
  name: string
  type: string
  mechanism: Record<string, string>
  inputs: IOField[]
  outputs: IOField[]
  preconditions: Predicate[]
  effects: Predicate[]
  constraints: Predicate[]
  resources: string[]
  cost: Cost
  reliability: number
  availability: number
  components: string[]
}

export type Scenario = {
  id: string
  name: string
  states: State[]
  goals: Goal[]
  capabilities: Capability[]
}

export type FeatureVector = Record<string, number>
export type EmbeddingResult = { entity_type: string; entity_id: string; vector: FeatureVector; dimension_count: number }
export type CompatibilityResult = {
  compatible: boolean
  producer_id: string
  consumer_id: string
  evidence: Array<Record<string, unknown> & { satisfied: boolean }>
  reasons: string[]
}
export type CompositionResult = {
  composite: Capability
  embedding: FeatureVector
  dimension_count: number
  compatibility_checks: CompatibilityResult[]
}
export type ExperimentReport = {
  scenario_id: string
  metrics: Record<string, number>
  experiments: Array<{ id: string; results?: Record<string, any>; skipped?: string; reason?: string }>
}
