import React, { useState, useEffect } from 'react';
import { Vector, Capability, STATE_VARS, DIMENSIONS } from './lib/embedding';
import {
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { Play, AlertCircle, Info } from 'lucide-react';

// ─── Constants ────────────────────────────────────────────────────────────────

const DEFAULT_INPUT = `{
  "name": "NotifyAdmin",
  "preconditions": {
    "User.role_ADMIN": 1,
    "Order.exists": 1
  },
  "effects": {
    "Notification.sent": 1
  },
  "cost": 0.05,
  "reliability": 0.99,
  "availability": 1.0
}`;

const TOOLTIP_STYLE = {
  contentStyle: {
    backgroundColor: '#0d1526',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: '10px',
    fontSize: '12px',
    color: '#f0f4ff',
    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
  },
  itemStyle: { color: '#8b9ab8' },
  labelStyle: { color: '#f0f4ff', fontWeight: 600 },
};

// Segment info for the full capability vector
const SEGMENTS = [
  { label: 'Preconditions', dims: DIMENSIONS, color: '#4f8cff', tag: 'tag-blue' },
  { label: 'Effects', dims: DIMENSIONS, color: '#9b6dff', tag: 'tag-violet' },
  { label: 'Operational', dims: 3, color: '#22d3ee', tag: 'tag-cyan', names: ['Cost', 'Reliability', 'Availability'] },
];

// ─── Component ────────────────────────────────────────────────────────────────

export default function Sandbox() {
  const [jsonInput, setJsonInput] = useState(DEFAULT_INPUT);
  const [capability, setCapability] = useState<Capability | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = () => {
    try {
      setError(null);
      const parsed = JSON.parse(jsonInput);

      const preMap: Record<string, number> = parsed.preconditions || {};
      const effMap: Record<string, number> = parsed.effects || {};

      const preVector = Vector.fromMap(preMap);
      const effVector = Vector.fromMap(effMap);

      const maskMap: Record<string, number> = {};
      Object.keys(effMap).forEach(k => { maskMap[k] = 1; });
      const maskVector = Vector.fromMap(maskMap);

      setCapability(new Capability(
        parsed.name || 'Unnamed',
        preVector,
        effVector,
        maskVector,
        parsed.cost ?? 0,
        parsed.reliability ?? 1,
        parsed.availability ?? 1,
      ));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Invalid JSON');
    }
  };

  useEffect(() => { handleGenerate(); }, []);

  // Build full embedding vector data for chart
  const chartData = capability
    ? (() => {
        const vec = capability.toVector();
        const shortNames = STATE_VARS.map(v => {
          const parts = v.split('.');
          return `${parts[0][0]}:${parts[1].replace('status_', '').slice(0, 5)}`;
        });

        const points: { name: string; value: number; color: string; segment: string }[] = [];

        // Preconditions
        for (let i = 0; i < DIMENSIONS; i++) {
          points.push({ name: shortNames[i], value: vec[i], color: '#4f8cff', segment: 'Pre' });
        }
        // Effects
        for (let i = 0; i < DIMENSIONS; i++) {
          points.push({ name: shortNames[i], value: vec[DIMENSIONS + i], color: '#9b6dff', segment: 'Eff' });
        }
        // Ops
        const opsNames = ['Cost', 'Reliability', 'Avail.'];
        for (let i = 0; i < 3; i++) {
          points.push({ name: opsNames[i], value: vec[DIMENSIONS * 2 + i], color: '#22d3ee', segment: 'Ops' });
        }
        return points;
      })()
    : [];

  const totalDims = DIMENSIONS * 2 + 3;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="page-header">
        <div className="page-title">Custom Embedding Sandbox</div>
        <div className="page-subtitle">
          Define any operation as a JSON payload. The system projects it into a unified {totalDims}-dimensional vector space.
        </div>
      </div>

      <div className="grid-2" style={{ gridTemplateColumns: '1fr 1.6fr' }}>
        {/* Input Panel */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="card-title">Define Your Operation</div>
              <div className="card-desc" style={{ marginTop: 4 }}>
                Provide preconditions, effects, and operational metrics.
              </div>
            </div>
          </div>

          {/* Schema hint */}
          <div className="insight-box info" style={{ fontSize: 12 }}>
            <strong>Valid state keys:</strong>{' '}
            {STATE_VARS.slice(0, 4).map(v => (
              <code key={v} style={{ fontSize: 11, marginRight: 4 }}>{v}</code>
            ))}
            <span style={{ color: '#4a5a7a' }}>+ {STATE_VARS.length - 4} more…</span>
          </div>

          <textarea
            className="json-textarea"
            value={jsonInput}
            onChange={e => setJsonInput(e.target.value)}
            spellCheck={false}
          />

          {error && (
            <div className="error-text">
              <AlertCircle size={14} /> {error}
            </div>
          )}

          <button className="btn btn-primary" onClick={handleGenerate}>
            <Play size={14} /> Generate Embedding
          </button>
        </div>

        {/* Chart */}
        <div className="card card-glow" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div className="card-title">
                {capability ? capability.name : '—'} Embedding Vector
              </div>
              <div className="card-desc">
                Full {totalDims}-dimensional representation
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              <span className="tag tag-blue">Pre ({DIMENSIONS}D)</span>
              <span className="tag tag-violet">Eff ({DIMENSIONS}D)</span>
              <span className="tag tag-cyan">Ops (3D)</span>
            </div>
          </div>

          {capability ? (
            <>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData} margin={{ top: 4, right: 4, left: -22, bottom: 28 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis
                    dataKey="name"
                    stroke="transparent"
                    tick={{ fill: '#4a5a7a', fontSize: 9 }}
                    angle={-40}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis stroke="transparent" tick={{ fill: '#4a5a7a', fontSize: 10 }} domain={[-1.2, 1.2]} tickCount={4} />
                  <Tooltip {...TOOLTIP_STYLE} />
                  <ReferenceLine y={0} stroke="rgba(255,255,255,0.1)" />
                  <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                    {chartData.map((entry, i) => (
                      <Cell key={i} fill={entry.value === 0 ? 'rgba(255,255,255,0.06)' : entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>

              {/* Raw vector */}
              <div>
                <div className="chart-title" style={{ marginBottom: 8 }}>
                  <Info size={12} /> Raw Embedding Vector φ(C)
                </div>
                <div className="code-block">
                  [{capability.toVector().map(v => v.toFixed(2)).join(', ')}]
                </div>
              </div>
            </>
          ) : (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 14 }}>
              Click "Generate Embedding" to visualize
            </div>
          )}
        </div>
      </div>

      {/* How it works */}
      <div className="card">
        <div className="card-title" style={{ marginBottom: 18 }}>How the Embedding Works</div>
        <div className="grid-3">
          {[
            {
              step: '1',
              title: 'State Domain Registration',
              desc: 'The system defines a global domain of ' + DIMENSIONS + ' boolean/continuous state variables (e.g. Order.exists, Payment.status_SUCCESS). Each variable occupies one index in the embedding.',
            },
            {
              step: '2',
              title: 'Sub-vector Projection',
              desc: 'Your JSON maps named keys → values. The precondition and effect maps are separately projected into two R^' + DIMENSIONS + ' sub-vectors via index lookup. Unspecified dimensions default to 0.',
            },
            {
              step: '3',
              title: 'Operational Scalar Append',
              desc: 'Cost, Reliability, and Availability are appended as continuous scalars, giving the full φ(C) ∈ R^' + totalDims + '. This enables cost-aware A* orchestration planning.',
            },
          ].map(({ step, title, desc }) => (
            <div key={step} className="step-item">
              <div className="step-number">{step}</div>
              <div className="step-body">
                <div className="step-title">{title}</div>
                <div className="step-desc">{desc}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="section-divider" style={{ margin: '20px 0' }} />

        {/* Segment breakdown */}
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {SEGMENTS.map(seg => (
            <div key={seg.label} className="stat-card" style={{ flex: 1, minWidth: 160 }}>
              <div className="stat-card-label">{seg.label}</div>
              <div className="stat-card-value" style={{ color: seg.color, fontSize: 28 }}>{seg.dims}</div>
              <div className="stat-card-sub">dimensions</div>
              {seg.names && (
                <div style={{ marginTop: 8, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {seg.names.map(n => (
                    <span key={n} className={`tag ${seg.tag}`} style={{ fontSize: 10 }}>{n}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
