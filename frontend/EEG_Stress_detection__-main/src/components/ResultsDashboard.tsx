import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AreaChart, Area, ResponsiveContainer, XAxis, YAxis,
  CartesianGrid, Tooltip,
} from 'recharts';
import {
  CheckCircle2, X as XIcon,
  Brain, TreePine, Zap, Network, Layers, ArrowDown,
} from 'lucide-react';
import SectionHeading from '@/components/primitives/SectionHeading';
import { deapModelResults, highlightMetrics, type Metric, type PerModelResult } from '@/data/config';
import type { ResultsContext } from '@/App';

type Props = {
  context: ResultsContext;
  onClose: () => void;
};

const fmt = (v: Metric, suffix = '') => (v === null ? '—' : `${v}${suffix}`);
const fmtPct = (v: Metric) => (v === null ? '—' : `${v}%`);

const modelIcons: Record<string, typeof Brain> = {
  svm: Brain,
  rf: TreePine,
  xgb: Zap,
  cnn: Network,
  lstmcnn: Layers,
};

const datasetNames: Record<string, string> = {
  deap: 'DEAP Benchmark Dataset',
  custom: 'Custom 15-Subject Collected Data',
};

export default function ResultsDashboard({ context, onClose }: Props) {
  const tabs = useMemo(() => deapModelResults.map((r) => ({ id: r.id, name: r.name })), []);
  const defaultTab = deapModelResults[0]?.id ?? 'svm';
  const [active, setActive] = useState<string>(defaultTab);

  useEffect(() => {
    if (context.modelTab) {
      const matched = tabs.find((t) => t.id === context.modelTab) ?? tabs[0];
      if (matched) setActive(matched.id);
    }
  }, [context.modelTab, tabs]);

  const activeModel = deapModelResults.find((m) => m.id === active) ?? deapModelResults[0];
  const showBanner = context.dataset !== null;
  const datasetLabel = context.dataset ? datasetNames[context.dataset] : null;

  return (
    <section id="results" className="relative py-24 sm:py-32 scroll-mt-20">
      <div className="section-pad">
        <SectionHeading
          eyebrow="Experimental Results"
          title="DEAP Model Performance Gallery"
          description="Interactive per-model results for the DEAP benchmark dataset. Click a model tab to inspect metrics, training curves, confusion matrices, and key findings."
          align="center"
        />

        {showBanner && datasetLabel && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mx-auto mt-6 flex max-w-5xl items-center justify-between gap-3 rounded-2xl border border-bio-400/30 bg-bio-500/10 px-5 py-3"
          >
            <div className="flex items-center gap-3 text-sm">
              <ArrowDown className="h-4 w-4 shrink-0 animate-bounce text-bio-300" />
              <span className="font-mono text-xs uppercase tracking-wider text-bio-300/70">Showing results for</span>
              <span className="font-semibold text-bio-100">{datasetLabel}</span>
            </div>
            <button
              onClick={onClose}
              className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-slate-300 transition-colors hover:bg-white/10 hover:text-white"
              aria-label="Clear filter"
              title="Clear dataset filter"
            >
              <XIcon className="h-3.5 w-3.5" />
            </button>
          </motion.div>
        )}

        {/* highlight metrics */}
        <div className="mx-auto mt-10 grid max-w-5xl gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {highlightMetrics.map((m, i) => (
            <motion.div
              key={m.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-40px' }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
              className="glass group relative overflow-hidden rounded-2xl p-6 text-center"
            >
              <div className="pointer-events-none absolute inset-x-0 -top-8 mx-auto h-16 w-16 rounded-full bg-signal-500/10 blur-2xl opacity-0 transition-opacity group-hover:opacity-100" />
              <p className="font-mono text-xs uppercase tracking-widest text-slate-500">{m.label}</p>
              <p className="mt-3 text-4xl font-semibold text-white">
                {fmt(m.value, m.suffix)}
              </p>
              <div className="mt-3 flex justify-center">
                <span className="h-1 w-10 rounded-full bg-gradient-to-r from-signal-400 to-violet-400" />
              </div>
            </motion.div>
          ))}
        </div>

        {/* model tabs */}
        <div className="mx-auto mt-12 max-w-5xl">
          <div className="mb-2 flex items-center justify-between">
            <p className="font-mono text-xs uppercase tracking-widest text-slate-500">Select Model</p>
            <p className="font-mono text-[0.7rem] text-slate-600">{tabs.length} models · DEAP Subject 01</p>
          </div>
          <div className="flex flex-wrap gap-2 rounded-2xl border border-signal-400/10 bg-ink-900/40 p-2">
            {tabs.map((t) => {
              const Icon = modelIcons[t.id] ?? Brain;
              const isActive = active === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => setActive(t.id)}
                  className={`group relative flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-300 ${
                    isActive
                      ? 'text-white'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {isActive && (
                    <motion.span
                      layoutId="results-model-tab"
                      className="absolute inset-0 rounded-xl bg-gradient-to-r from-signal-500/25 to-violet-500/20 border border-signal-400/30 shadow-[0_0_30px_-10px_rgba(72,120,255,0.4)]"
                      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                    />
                  )}
                  <span className="relative z-10">
                    <Icon className="h-4 w-4" />
                  </span>
                  <span className="relative z-10">{t.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* per-model content */}
        <div className="mx-auto mt-8 max-w-5xl">
          <AnimatePresence mode="wait">
            {activeModel && (
              <ModelPanel key={activeModel.id} model={activeModel} />
            )}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}

function ModelPanel({ model }: { model: PerModelResult }) {
  const metrics = [
    { label: 'Accuracy', value: model.accuracy, suffix: '%', accent: 'text-signal-300' },
    { label: 'Precision', value: model.precision, suffix: '', accent: 'text-bio-300' },
    { label: 'Recall', value: model.recall, suffix: '', accent: 'text-violet-300' },
    { label: 'F1 Score', value: model.f1, suffix: '', accent: 'text-emerald-300' },
  ];
  const pending = model.accuracy === null;

  return (
    <motion.div
      key={model.id}
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.35 }}
      className="glass rounded-2xl p-5 sm:p-7"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-signal-400/30 bg-signal-500/10 text-signal-300">
              {(() => {
                const Icon = modelIcons[model.id] ?? Brain;
                return <Icon className="h-4.5 w-4.5" />;
              })()}
            </span>
            <div>
              <h3 className="text-lg font-semibold text-white">{model.name}</h3>
              <p className="font-mono text-xs text-slate-500">{model.tagline}</p>
            </div>
          </div>
        </div>
        {pending && (
          <span className="rounded-full border border-amber-400/30 bg-amber-500/10 px-3 py-1 text-xs text-amber-300">
            Pending — results not yet available
          </span>
        )}
      </div>

      {/* metric cards */}
      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {metrics.map((m) => (
          <div key={m.label} className="rounded-xl border border-white/5 bg-ink-950/50 px-4 py-4">
            <p className="font-mono text-[0.65rem] uppercase tracking-wider text-slate-500">{m.label}</p>
            <p className={`mt-1.5 text-2xl font-semibold ${pending ? 'text-slate-600' : m.accent}`}>
              {m.value === null ? '—' : (m.label === 'Accuracy' ? `${m.value}%` : `${m.value}`.padEnd(4, '0').slice(0, 4))}
            </p>
          </div>
        ))}
      </div>

      {/* charts + confusion matrix */}
      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <ChartCard title="Training Curve" subtitle="Accuracy per epoch (scaled)">
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={model.trainingCurve} margin={{ top: 10, right: 10, left: -24, bottom: 0 }}>
              <defs>
                <linearGradient id={`acc-${model.id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#4878ff" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#4878ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(124,165,255,0.08)" />
              <XAxis dataKey="epoch" stroke="#475569" fontSize={11} tickLine={false} />
              <YAxis stroke="#475569" fontSize={11} tickLine={false} domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  background: '#0b0e1a',
                  border: '1px solid rgba(124,165,255,0.2)',
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(val: unknown) => {
                  if (val === null || val === undefined) return '—';
                  if (typeof val === 'number') return `${val}%`;
                  return String(val);
                }}
              />
              <Area
                type="monotone"
                dataKey="acc"
                stroke="#4878ff"
                strokeWidth={2}
                fill={`url(#acc-${model.id})`}
                connectNulls
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Confusion Matrix" subtitle="Actual (rows) × Predicted (cols)">
          <ConfusionMatrix cm={model.confusion} pending={pending} />
        </ChartCard>
      </div>

      {/* highlights */}
      <div className="mt-6 rounded-xl border border-white/5 bg-ink-950/40 p-5">
        <p className="mb-3 flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-slate-500">
          <CheckCircle2 className="h-3.5 w-3.5 text-signal-300" /> Key Findings
        </p>
        <ul className="space-y-2">
          {model.highlights.map((h, i) => (
            <motion.li
              key={i}
              initial={{ opacity: 0, x: -8 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.3, delay: i * 0.06 }}
              className="flex items-start gap-2.5 text-sm text-slate-300"
            >
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-signal-400" />
              <span>{h}</span>
            </motion.li>
          ))}
        </ul>
      </div>
    </motion.div>
  );
}

function ChartCard({ title, subtitle, children }: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-white/5 bg-ink-950/40 p-5">
      <div className="mb-3">
        <h4 className="text-sm font-semibold text-white">{title}</h4>
        <p className="font-mono text-xs text-slate-500">{subtitle}</p>
      </div>
      {children}
    </div>
  );
}

function ConfusionMatrix({ cm, pending }: {
  cm: { tp: Metric; fp: Metric; tn: Metric; fn: Metric };
  pending: boolean;
}) {
  const cell = (v: Metric, strong: boolean) => (
    <div
      className={`flex h-20 items-center justify-center rounded-lg border text-lg font-semibold ${
        pending
          ? 'border-white/5 bg-ink-900/60 text-slate-600'
          : strong
            ? 'border-emerald-400/30 bg-emerald-500/10 text-emerald-300'
            : 'border-rose-400/30 bg-rose-500/10 text-rose-300'
      }`}
    >
      {v === null ? '—' : v}
    </div>
  );

  return (
    <div className="mx-auto max-w-sm">
      <div className="mb-1.5 grid grid-cols-[56px_1fr_1fr] gap-1.5 font-mono text-[0.65rem] uppercase tracking-wider text-slate-500">
        <div />
        <div className="text-center">Pred Relaxed</div>
        <div className="text-center">Pred Stress</div>
      </div>
      <div className="grid grid-cols-[56px_1fr_1fr] items-center gap-1.5 font-mono text-[0.65rem] uppercase tracking-wider text-slate-500">
        <div className="pr-1 text-right">Actual R</div>
        {cell(cm.tn, true)}
        {cell(cm.fp, false)}
      </div>
      <div className="mt-1.5 grid grid-cols-[56px_1fr_1fr] items-center gap-1.5 font-mono text-[0.65rem] uppercase tracking-wider text-slate-500">
        <div className="pr-1 text-right">Actual S</div>
        {cell(cm.fn, false)}
        {cell(cm.tp, true)}
      </div>
      <div className="mt-3 flex items-center justify-center gap-4 text-[10px] text-slate-500">
        <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-sm bg-emerald-400/60" /> Correct</span>
        <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-sm bg-rose-400/60" /> Error</span>
      </div>
    </div>
  );
}
