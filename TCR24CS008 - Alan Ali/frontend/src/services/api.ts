import type {
  Capability,
  CompatibilityResult,
  CompositionResult,
  EmbeddingResult,
  ExperimentReport,
  Goal,
  Scenario,
  State,
} from '../types'

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? 'http://127.0.0.1:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { ...(init?.body ? { 'Content-Type': 'application/json' } : {}), ...init?.headers },
    })
  } catch {
    throw new Error(`Cannot reach the backend at ${API_BASE}. Start the FastAPI server and retry.`)
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail
    const message = typeof detail === 'string' ? detail : detail?.message ?? JSON.stringify(detail ?? response.statusText)
    throw new Error(`${response.status}: ${message}`)
  }
  return response.json() as Promise<T>
}

const post = (path: string, body: unknown) => request(path, { method: 'POST', body: JSON.stringify(body) })

export const api = {
  baseUrl: API_BASE,
  health: () => request<{ status: string }>('/api/health'),
  getScenario: () => request<Scenario>('/api/scenario'),
  saveScenario: (scenario: Scenario) => post('/api/scenario', scenario) as Promise<Scenario>,
  encodeState: (state: State) => post('/api/encode/state', state) as Promise<EmbeddingResult>,
  encodeGoal: (goal: Goal) => post('/api/encode/goal', goal) as Promise<EmbeddingResult>,
  encodeCapability: (capability: Capability) => post('/api/encode/capability', capability) as Promise<EmbeddingResult>,
  compareCapabilities: (left: Capability, right: Capability) => post('/api/similarity/capabilities', { capabilities: [left, right] }) as Promise<{
    similarity: number; metric: string; section_scores: Record<string, { similarity: number; weight: number }>
  }>,
  compatibility: (producer: Capability, consumer: Capability) => post('/api/compatibility', { producer, consumer }) as Promise<CompatibilityResult>,
  compose: (capabilities: Capability[]) => post('/api/compose', { capabilities }) as Promise<CompositionResult>,
  applicability: (state: State, capability: Capability) => post('/api/applicability', { state, capability }) as Promise<{
    applicable: boolean; evidence: Array<{ predicate: Record<string, unknown>; satisfied: boolean }>
  }>,
  stateGoal: (state: State, goal: Goal) => post('/api/state-goal', { state, goal }) as Promise<{
    satisfied: boolean; evidence: Array<{ condition: Record<string, unknown>; satisfied: boolean }>
  }>,
  goalRelevance: (capability: Capability, goal: Goal) => post('/api/goal-relevance', { capability, goal }) as Promise<{
    relevant: boolean; matched_goal_variables: string[]; goal_effect_coverage: number; goal_effect_similarity: number
  }>,
  experiments: () => request<ExperimentReport>('/api/experiments'),
}
