import { useState, useMemo } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  FlaskConical,
  Layers,
  ArrowRight,
  CheckCircle,
  XCircle,
  Cpu,
  BarChart2,
  Activity,
  Zap,
  GitMerge,
  SlidersHorizontal,
  Brain,
} from 'lucide-react';
import {
  Vector,
  Capability,
  STATE_VARS,
  DIMENSIONS,
  isCompatible,
  compose,
  similarity,
} from './lib/embedding';
import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
} from 'recharts';
import Sandbox from './Sandbox';
import './index.css';

// ─── Domain Data ────────────────────────────────────────────────────────────

const createOrder = new Capability(
  'CreateOrder',
  Vector.fromMap({ 'Cart.item_count': 1 }),
  Vector.fromMap({ 'Order.exists': 1, 'Order.status_CREATED': 1 }),
  Vector.fromMap({ 'Order.exists': 1, 'Order.status_CREATED': 1 }),
  0.05, 0.99, 1.0
);

const makePayment = new Capability(
  'MakePayment',
  Vector.fromMap({ 'Order.exists': 1 }),
  Vector.fromMap({ 'Payment.status_SUCCESS': 1, 'Order.status_PAID': 1 }),
  Vector.fromMap({ 'Payment.status_SUCCESS': 1, 'Order.status_PAID': 1, 'Order.status_CREATED': 1 }),
  0.1, 0.95, 0.99
);

const cancelCart = new Capability(
  'CancelCart',
  Vector.fromMap({ 'Order.exists': -1 }),
  Vector.fromMap({ 'Cart.exists': -1 }),
  Vector.fromMap({ 'Cart.exists': 1 }),
  0.01, 1.0, 1.0
);

const makePaymentAPI = new Capability(
  'MakePayment (API)',
  Vector.fromMap({ 'Order.exists': 1 }),
  Vector.fromMap({ 'Payment.status_SUCCESS': 1 }),
  Vector.fromMap({ 'Payment.status_SUCCESS': 1 }),
  0.2, 0.98, 0.99
);

const makePaymentGUI = new Capability(
  'MakePayment (GUI)',
  Vector.fromMap({ 'Order.exists': 1 }),
  Vector.fromMap({ 'Payment.status_SUCCESS': 1 }),
  Vector.fromMap({ 'Payment.status_SUCCESS': 1 }),
  0.0, 0.95, 0.90
);

const sendNewsletter = new Capability(
  'SendNewsletter',
  Vector.fromMap({ 'User.authenticated': 1 }),
  Vector.fromMap({ 'Notification.sent': 1 }),
  Vector.fromMap({ 'Notification.sent': 1 }),
  0.01, 0.99, 1.0
);

// ─── Chart Colors ────────────────────────────────────────────────────────────

const CHART_COLORS = {
  blue: '#4f8cff',
  violet: '#9b6dff',
  cyan: '#22d3ee',
  green: '#10d88a',
  amber: '#f59e0b',
};

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
  labelStyle: { color: '#f0f4ff', fontWeight: 600, marginBottom: 4 },
};

// ─── Shared Components ────────────────────────────────────────────────────────

const SHORT_NAMES = STATE_VARS.map(v => {
  const parts = v.split('.');
  const prefix = parts[0][0];
  const suffix = parts[1].replace('status_', '').slice(0, 5);
  return `${prefix}:${suffix}`;
});

function VectorBar({ vector, gradient }: { vector: Vector; gradient: string }) {
  const data = STATE_VARS.map((_, i) => ({
    name: SHORT_NAMES[i],
    value: vector.values[i],
  }));

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 18 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
        <XAxis
          dataKey="name"
          stroke="transparent"
          tick={{ fill: '#4a5a7a', fontSize: 9.5 }}
          angle={-40}
          textAnchor="end"
          interval={0}
        />
        <YAxis stroke="transparent" tick={{ fill: '#4a5a7a', fontSize: 10 }} tickCount={3} domain={[-1.2, 1.2]} />
        <Tooltip {...TOOLTIP_STYLE} />
        <ReferenceLine y={0} stroke="rgba(255,255,255,0.1)" />
        <Bar dataKey="value" radius={[3, 3, 0, 0]}>
          {data.map((entry, i) => (
            <Cell
              key={i}
              fill={entry.value > 0 ? CHART_COLORS.blue : entry.value < 0 ? CHART_COLORS.amber : 'rgba(255,255,255,0.06)'}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function VectorCard({ cap, showPre = true, showEff = true }: { cap: Capability; showPre?: boolean; showEff?: boolean }) {
  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="card-title" style={{ fontSize: 15, marginBottom: 0 }}>{cap.name}</div>
        <div style={{ display: 'flex', gap: 6 }}>
          <span className="tag tag-amber">cost: {cap.cost}</span>
          <span className="tag tag-green">rel: {(cap.reliability * 100).toFixed(0)}%</span>
        </div>
      </div>
      {showPre && (
        <div>
          <div className="chart-title" style={{ color: '#7aa9ff' }}>
            <BarChart2 size={13} /> Preconditions
          </div>
          <VectorBar vector={cap.preconditions} gradient="blue" />
        </div>
      )}
      {showEff && (
        <div>
          <div className="chart-title" style={{ color: '#b89aff' }}>
            <Activity size={13} /> Effects
          </div>
          <VectorBar vector={cap.effects} gradient="violet" />
        </div>
      )}
    </div>
  );
}

// ─── Tab Panels ───────────────────────────────────────────────────────────────

function CompatPanel() {
  const c1c2 = isCompatible(createOrder, makePayment);
  const c1c3 = isCompatible(createOrder, cancelCart);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="page-header">
        <div className="page-title">Capability Compatibility</div>
        <div className="page-subtitle">Checking if C1's effects satisfy C2 or C3's preconditions using vector algebra.</div>
      </div>

      <div className="grid-2">
        <div className="card card-glow" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="card-title">Compatibility Results</div>
          <div className="card-desc">
            C1 effects are crossed with C2/C3 preconditions. A conflict arises if any dimension's sign is inverted.
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
            {[
              { label: 'C1 (CreateOrder)', arrow: '→', target: 'C2 (MakePayment)', ok: c1c2 },
              { label: 'C1 (CreateOrder)', arrow: '→', target: 'C3 (CancelCart)', ok: c1c3 },
            ].map((r, i) => (
              <div key={i} className="result-row">
                <div className="result-label">
                  <span>{r.label}</span>{' '}
                  <span style={{ color: '#4a5a7a', margin: '0 6px' }}>{r.arrow}</span>
                  <span>{r.target}</span>
                </div>
                <div className={`status-pill ${r.ok ? 'compatible' : 'incompatible'}`}>
                  {r.ok ? <CheckCircle size={12} /> : <XCircle size={12} />}
                  {r.ok ? 'Compatible' : 'Incompatible'}
                </div>
              </div>
            ))}
          </div>
          <div className="insight-box info" style={{ marginTop: 8 }}>
            <strong>Why?</strong> C1 sets <code>Order.exists = 1</code>. C2 requires it as <code>+1</code> (match ✓). C3 requires <code>Order.exists = −1</code> (conflict ✗).
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div className="card-title">Compatibility Formula</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div className="step-item">
              <div className="step-number">1</div>
              <div className="step-body">
                <div className="step-title">Conflict Check</div>
                <div className="step-desc">For each dimension <em>j</em>: if <code>pre₂[j] &gt; 0</code> and <code>eff₁[j] &lt; 0</code> → CONFLICT.</div>
              </div>
            </div>
            <div className="step-item">
              <div className="step-number">2</div>
              <div className="step-body">
                <div className="step-title">Provides Check</div>
                <div className="step-desc">C1 must supply at least one positive requirement of C2: <code>pre₂[j] &gt; 0 ∧ eff₁[j] &gt; 0</code></div>
              </div>
            </div>
            <div className="step-item">
              <div className="step-number">3</div>
              <div className="step-body">
                <div className="step-title">Result</div>
                <div className="step-desc"><code>compatible = !conflict ∧ provides</code></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        <VectorCard cap={createOrder} showPre={false} />
        <VectorCard cap={cancelCart} showEff={false} />
      </div>
    </div>
  );
}

function ComposePanel() {
  const composite = useMemo(() => compose(createOrder, makePayment), []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="page-header">
        <div className="page-title">Capability Composition</div>
        <div className="page-subtitle">Algebraically fusing C1 and C2 into a single atomic composite capability C₁₂.</div>
      </div>

      <div className="card card-glow">
        <div className="card-title" style={{ marginBottom: 16 }}>Composition Pipeline</div>
        <div className="flow-diagram">
          <div className="flow-node">
            <div className="flow-node-box blue">CreateOrder</div>
            <div className="flow-node-label">C1 · cost: 0.05 · rel: 99%</div>
          </div>
          <div className="flow-arrow">
            <div className="flow-arrow-line" />
            <ArrowRight size={14} style={{ color: '#4f8cff', marginTop: -7 }} />
          </div>
          <div className="flow-node">
            <div className="flow-node-box violet">MakePayment</div>
            <div className="flow-node-label">C2 · cost: 0.10 · rel: 95%</div>
          </div>
          <div className="flow-arrow">
            <div className="flow-arrow-line" />
            <ArrowRight size={14} style={{ color: '#9b6dff', marginTop: -7 }} />
          </div>
          <div className="flow-node">
            <div className="flow-node-box green">CompletePurchase</div>
            <div className="flow-node-label">C₁₂ · cost: {composite.cost.toFixed(2)} · rel: {(composite.reliability * 100).toFixed(1)}%</div>
          </div>
        </div>
      </div>

      <div className="grid-3">
        {[
          { cap: createOrder, label: 'C1 Preconditions', vec: createOrder.preconditions, color: CHART_COLORS.blue },
          { cap: makePayment, label: 'C2 Effects', vec: makePayment.effects, color: CHART_COLORS.violet },
          { cap: composite, label: 'C₁₂ Composite Preconditions', vec: composite.preconditions, color: CHART_COLORS.green },
        ].map(({ label, vec, color }, i) => (
          <div key={i} className="card">
            <div className="chart-title" style={{ color }}>{label}</div>
            <VectorBar vector={vec} gradient="blue" />
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-title" style={{ marginBottom: 14 }}>Composition Algebra</div>
        <div className="grid-3" style={{ gap: 14 }}>
          <div>
            <div className="step-item">
              <div className="step-number">P</div>
              <div className="step-body">
                <div className="step-title">Composite Preconditions</div>
                <div className="step-desc"><code>pre₁₂[j] = max(pre₁[j], pre₂[j] − eff₁[j])</code> — merges what C1 needs with what C2 still needs after C1 executes.</div>
              </div>
            </div>
          </div>
          <div>
            <div className="step-item">
              <div className="step-number">E</div>
              <div className="step-body">
                <div className="step-title">Composite Effects</div>
                <div className="step-desc"><code>eff₁₂[j] = eff₂[j] if mask₂[j]=1 else eff₁[j]</code> — C2 overwrites, C1 persists elsewhere.</div>
              </div>
            </div>
          </div>
          <div>
            <div className="step-item">
              <div className="step-number">O</div>
              <div className="step-body">
                <div className="step-title">Operational Metrics</div>
                <div className="step-desc"><code>cost = c₁+c₂, rel = r₁·r₂</code> — additive cost, multiplicative reliability degradation.</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AltPanel() {
  const sim = similarity(makePaymentAPI, makePaymentGUI);

  const radarData = [
    { attr: 'Precond', api: makePaymentAPI.preconditions.values[0], gui: makePaymentGUI.preconditions.values[0] },
    { attr: 'Effect', api: makePaymentAPI.effects.values[3], gui: makePaymentGUI.effects.values[3] },
    { attr: 'Cost', api: 1 - makePaymentAPI.cost, gui: 1 - makePaymentGUI.cost },
    { attr: 'Reliability', api: makePaymentAPI.reliability, gui: makePaymentGUI.reliability },
    { attr: 'Availability', api: makePaymentAPI.availability, gui: makePaymentGUI.availability },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="page-header">
        <div className="page-title">Alternative Implementations</div>
        <div className="page-subtitle">Two capabilities with identical functional signatures but different operational profiles.</div>
      </div>

      <div className="grid-2">
        <div className="card card-glow" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card-title">Cosine Similarity</div>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12, marginTop: 4 }}>
            <div style={{ fontSize: 48, fontWeight: 800, letterSpacing: -2, color: '#f0f4ff', lineHeight: 1 }}>
              {(sim * 100).toFixed(1)}
              <span style={{ fontSize: 18, color: '#4f8cff', fontWeight: 600 }}>%</span>
            </div>
            <div style={{ color: '#8b9ab8', fontSize: 13, marginBottom: 6 }}>functional similarity</div>
          </div>
          <div className="progress-bar-wrap" style={{ marginTop: 4 }}>
            <div className="progress-bar-fill" style={{ width: `${sim * 100}%` }} />
          </div>
          <div className="insight-box info" style={{ marginTop: 4 }}>
            Near-identical functional embedding — differing only in <strong>cost</strong> and <strong>reliability</strong> dimensions.
          </div>
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Operational Comparison</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
              { label: 'Cost per call', api: '$0.20', gui: '$0.00', winner: 'gui' },
              { label: 'Reliability', api: '98%', gui: '95%', winner: 'api' },
              { label: 'Availability', api: '99%', gui: '90%', winner: 'api' },
            ].map((row, i) => (
              <div key={i} className="result-row">
                <span className="result-label">{row.label}</span>
                <div style={{ display: 'flex', gap: 12 }}>
                  <span className={`tag ${row.winner === 'api' ? 'tag-green' : 'tag-blue'}`}>API: {row.api}</span>
                  <span className={`tag ${row.winner === 'gui' ? 'tag-green' : 'tag-blue'}`}>GUI: {row.gui}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title" style={{ marginBottom: 16 }}>Attribute Radar</div>
        <ResponsiveContainer width="100%" height={240}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="rgba(255,255,255,0.06)" />
            <PolarAngleAxis dataKey="attr" tick={{ fill: '#8b9ab8', fontSize: 12 }} />
            <Radar name="API" dataKey="api" stroke={CHART_COLORS.blue} fill={CHART_COLORS.blue} fillOpacity={0.15} strokeWidth={2} />
            <Radar name="GUI" dataKey="gui" stroke={CHART_COLORS.violet} fill={CHART_COLORS.violet} fillOpacity={0.15} strokeWidth={2} />
            <Tooltip {...TOOLTIP_STYLE} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function OpsPanel() {
  const goal = Vector.fromMap({ 'Payment.status_SUCCESS': 1 });
  const dotGoal = sendNewsletter.effects.dot(goal);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="page-header">
        <div className="page-title">Operational Attributes & Irrelevance</div>
        <div className="page-subtitle">Embedding cost/reliability enables optimal planning. Dot-product filtering eliminates irrelevant capabilities.</div>
      </div>

      <div className="grid-2">
        <div className="card card-glow" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card-title">Irrelevant Capability Detection</div>
          <div className="card-desc">
            Goal: <code>Payment.status_SUCCESS = 1</code>. SendNewsletter only sets <code>Notification.sent = 1</code>.
          </div>
          <div className="result-row" style={{ marginTop: 8 }}>
            <span className="result-label">SendNewsletter · goal dot product</span>
            <span className="tag tag-amber" style={{ fontSize: 13 }}>= {dotGoal}</span>
          </div>
          <div className="insight-box warning">
            Dot product = 0 → orthogonal to goal → automatically pruned from orchestration graph.
          </div>
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>Capability Cost–Reliability Matrix</div>
          <div className="grid-2" style={{ gap: 12 }}>
            {[
              { name: 'CreateOrder', cost: 0.05, rel: 99, tag: 'blue' },
              { name: 'MakePayment', cost: 0.10, rel: 95, tag: 'violet' },
              { name: 'API Payment', cost: 0.20, rel: 98, tag: 'cyan' },
              { name: 'GUI Payment', cost: 0.00, rel: 95, tag: 'green' },
            ].map((cap, i) => (
              <div key={i} className="stat-card">
                <div className="stat-card-label">{cap.name}</div>
                <div className="stat-card-value" style={{ fontSize: 18, color: cap.tag === 'blue' ? CHART_COLORS.blue : cap.tag === 'violet' ? CHART_COLORS.violet : cap.tag === 'cyan' ? CHART_COLORS.cyan : CHART_COLORS.green }}>
                  {cap.rel}%
                </div>
                <div className="stat-card-sub">Cost: ${cap.cost.toFixed(2)} per call</div>
                <div className="progress-bar-wrap" style={{ marginTop: 10 }}>
                  <div className="progress-bar-fill" style={{ width: `${cap.rel}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Navigation Config ────────────────────────────────────────────────────────

type Tab = 'sandbox' | 'compat' | 'compose' | 'alt' | 'ops';

const NAV: { id: Tab; label: string; icon: React.ComponentType<any>; desc: string }[] = [
  { id: 'sandbox', label: 'Custom Sandbox', icon: SlidersHorizontal, desc: 'Define & embed your own data' },
  { id: 'compat', label: 'Compatibility', icon: Zap, desc: 'Check sequential composition rules' },
  { id: 'compose', label: 'Composition', icon: GitMerge, desc: 'Build composite capabilities' },
  { id: 'alt', label: 'Alternative Impl.', icon: Layers, desc: 'Compare functional similarity' },
  { id: 'ops', label: 'Ops & Irrelevance', icon: Activity, desc: 'Cost, reliability & goal filtering' },
];

// ─── App ─────────────────────────────────────────────────────────────────────

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('sandbox');

  const panel = {
    sandbox: <Sandbox />,
    compat: <CompatPanel />,
    compose: <ComposePanel />,
    alt: <AltPanel />,
    ops: <OpsPanel />,
  }[activeTab];

  return (
    <div className="app-layout">
      {/* Topbar */}
      <header className="topbar">
        <div className="topbar-brand">
          <div className="topbar-logo">
            <Brain size={16} />
          </div>
          <div>
            <div className="topbar-title">CapabilityEmbed</div>
            <div className="topbar-subtitle">Vector Embedding for Application Orchestration</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span className="tag tag-blue"><Cpu size={10} /> PCCST503 Assignment 2</span>
          <span className="tag tag-green"><FlaskConical size={10} /> {DIMENSIONS}D State Space</span>
        </div>
      </header>

      {/* Sidebar */}
      <nav className="sidebar">
        <div className="sidebar-section-label">Experiments</div>
        {NAV.map(({ id, label, icon: Icon, desc }) => (
          <button
            key={id}
            className={`nav-item ${activeTab === id ? 'active' : ''}`}
            onClick={() => setActiveTab(id)}
          >
            <span className="nav-item-icon"><Icon size={16} /></span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13.5, fontWeight: 600 }}>{label}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 1 }}>{desc}</div>
            </div>
            <span className="nav-item-dot" />
          </button>
        ))}

        <div className="section-divider" style={{ margin: '12px 0' }} />
        <div className="sidebar-section-label">Domain</div>
        <div style={{ padding: '8px 12px', display: 'flex', flexDirection: 'column', gap: 6 }}>
          {[
            { label: 'State Variables', val: DIMENSIONS, color: 'blue' },
            { label: 'Embed Dims', val: DIMENSIONS * 2 + 3, color: 'violet' },
            { label: 'Capabilities', val: 6, color: 'cyan' },
          ].map(({ label, val, color }) => (
            <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{label}</span>
              <span className={`tag tag-${color}`} style={{ fontSize: 11 }}>{val}</span>
            </div>
          ))}
        </div>
      </nav>

      {/* Main */}
      <main className="main-content">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
          >
            {panel}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
