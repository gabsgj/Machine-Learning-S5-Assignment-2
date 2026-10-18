import { useMemo, useState } from 'react'
import { ChevronDown, ChevronRight, Search } from 'lucide-react'
import type { FeatureVector } from '../types'
import { featureGroup } from '../utils/format'

export function FeatureVectorView({ vector }: { vector: FeatureVector }) {
  const [filter, setFilter] = useState('')
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({})
  const groups = useMemo(() => Object.entries(vector).filter(([key]) => key.toLowerCase().includes(filter.toLowerCase()))
    .reduce<Record<string, Array<[string, number]>>>((acc, item) => {
      const group = featureGroup(item[0])
      ;(acc[group] ??= []).push(item)
      return acc
    }, {}), [vector, filter])
  const sorted = Object.entries(groups).sort(([a], [b]) => a.localeCompare(b))

  if (!Object.keys(vector).length) return <div className="muted-note">This embedding has no active dimensions.</div>
  return <div className="vector-view">
    <label className="search-field"><Search size={15} /><input value={filter} onChange={(event) => setFilter(event.target.value)} placeholder="Filter dimensions" /></label>
    <div className="vector-groups">
      {sorted.map(([group, entries]) => {
        const open = openGroups[group] ?? true
        return <div className="vector-group" key={group}>
          <button className="vector-group-heading" onClick={() => setOpenGroups((current) => ({ ...current, [group]: !open }))}>
            {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}<span>{group}</span><small>{entries.length}</small>
          </button>
          {open && <div className="vector-rows">{entries.sort(([a], [b]) => a.localeCompare(b)).map(([key, value]) => <div className="vector-row" key={key}>
            <span title={key}>{key.slice(key.indexOf(':') + 1)}</span><strong>{Number(value.toFixed(4))}</strong>
          </div>)}</div>}
        </div>
      })}
    </div>
  </div>
}
