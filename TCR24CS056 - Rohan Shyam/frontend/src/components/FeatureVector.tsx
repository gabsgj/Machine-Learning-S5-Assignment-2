import { useId, useMemo, useState } from 'react'
import { ChevronDown, ChevronRight, Search } from 'lucide-react'
import type { FeatureVector } from '../types'
import { featureGroup } from '../utils/format'

type VectorEntry = [key: string, value: number]
type VectorGroups = Array<[group: string, entries: VectorEntry[]]>

export function FeatureVectorView({ vector }: { vector: FeatureVector }) {
  const [filter, setFilter] = useState('')
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({})
  const searchId = useId()
  const groups = useMemo<VectorGroups>(() => {
    const grouped = Object.entries(vector)
      .filter(([key]) => key.toLowerCase().includes(filter.toLowerCase()))
      .reduce<Record<string, VectorEntry[]>>((accumulator, entry) => {
        const group = featureGroup(entry[0])
        ;(accumulator[group] ??= []).push(entry)
        return accumulator
      }, {})

    return Object.entries(grouped)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([group, entries]) => [group, entries.sort(([left], [right]) => left.localeCompare(right))])
  }, [vector, filter])

  if (!Object.keys(vector).length) return <div className="muted-note">This embedding has no active dimensions.</div>
  return <div className="vector-view">
    <label className="search-field" htmlFor={searchId}><Search size={15} aria-hidden="true" /><span className="sr-only">Filter dimensions</span><input id={searchId} value={filter} onChange={(event) => setFilter(event.target.value)} placeholder="Filter dimensions" /></label>
    <div className="vector-groups">
      {groups.map(([group, entries]) => <FeatureVectorGroup
        key={group}
        group={group}
        entries={entries}
        open={openGroups[group] ?? true}
        onToggle={() => setOpenGroups((current) => ({ ...current, [group]: !(current[group] ?? true) }))}
      />)}
    </div>
  </div>
}

function FeatureVectorGroup({ group, entries, open, onToggle }: { group: string; entries: VectorEntry[]; open: boolean; onToggle: () => void }) {
  const contentId = `vector-group-${group.replace(/[^a-z0-9]+/gi, '-')}`
  return <div className="vector-group">
    <button type="button" className="vector-group-heading" aria-expanded={open} aria-controls={contentId} onClick={onToggle}>
      {open ? <ChevronDown size={15} aria-hidden="true" /> : <ChevronRight size={15} aria-hidden="true" />}<span>{group}</span><small>{entries.length}</small>
    </button>
    <div className="vector-rows" id={contentId} hidden={!open}>{entries.map(([key, value]) => <div className="vector-row" key={key}>
      <span title={key}>{key.slice(key.indexOf(':') + 1)}</span><strong>{Number(value.toFixed(4))}</strong>
    </div>)}</div>
  </div>
}
