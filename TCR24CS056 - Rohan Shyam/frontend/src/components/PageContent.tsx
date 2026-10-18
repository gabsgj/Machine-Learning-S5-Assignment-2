import { CapabilitiesPage } from '../pages/CapabilitiesPage'
import { CompositionPage } from '../pages/CompositionPage'
import { ExperimentsPage } from '../pages/ExperimentsPage'
import { OverviewPage } from '../pages/OverviewPage'
import { RelationshipsPage } from '../pages/RelationshipsPage'
import { ScenarioPage } from '../pages/ScenarioPage'
import type { PageId } from './Sidebar'
import type { Scenario } from '../types'
import type { Notify } from '../pages/types'

export type PageContentProps = {
  page: PageId
  scenario: Scenario
  notify: Notify
  onNavigate: (page: PageId) => void
  onScenario: (scenario: Scenario) => void
  onLoadExample: (scenario: Scenario, name: string) => Promise<void>
  loadedExample: string | null
  experimentRequest: number
}

export function PageContent({
  page,
  scenario,
  notify,
  onNavigate,
  onScenario,
  onLoadExample,
  loadedExample,
  experimentRequest,
}: PageContentProps) {
  return <main className="page-content" key={page}>
    {page === 'overview' && <OverviewPage scenario={scenario} onNavigate={onNavigate} />}
    {page === 'capabilities' && <CapabilitiesPage scenario={scenario} notify={notify} />}
    {page === 'relationships' && <RelationshipsPage scenario={scenario} notify={notify} />}
    {page === 'composition' && <CompositionPage scenario={scenario} notify={notify} />}
    {page === 'experiments' && <ExperimentsPage scenario={scenario} notify={notify} autoRunToken={experimentRequest} />}
    {page === 'scenario' && <ScenarioPage scenario={scenario} onScenario={onScenario} notify={notify} onLoadExample={onLoadExample} loadedExample={loadedExample} />}
    <footer className="page-footer"><span>Capability Composition</span><span>Formal feature vectors · Backend-computed results</span></footer>
  </main>
}
