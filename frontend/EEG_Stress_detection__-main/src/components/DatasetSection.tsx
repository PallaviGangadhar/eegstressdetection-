import { motion } from 'framer-motion';
import { Database, GitBranch, Cpu, ArrowRight, Sparkles } from 'lucide-react';
import SectionHeading from '@/components/primitives/SectionHeading';
import ECGWave from '@/components/primitives/ECGWave';
import EEGWave from '@/components/primitives/EEGWave';
import { datasets, type Dataset } from '@/data/config';

type Props = {
  onDatasetClick: (dataset: 'deap' | 'custom', modelTab: string) => void;
};

const accentMap = {
  signal: { text: 'text-signal-300', border: 'border-signal-400/30', bg: 'bg-signal-500/10', wave: '#4878ff', dot: 'bg-signal-400', ring: 'ring-signal-400/40' },
  bio: { text: 'text-bio-300', border: 'border-bio-400/30', bg: 'bg-bio-500/10', wave: '#38bdf8', dot: 'bg-bio-400', ring: 'ring-bio-400/40' },
  violet: { text: 'text-violet-300', border: 'border-violet-400/30', bg: 'bg-violet-500/10', wave: '#a78bfa', dot: 'bg-violet-400', ring: 'ring-violet-400/40' },
} as const;

export default function DatasetSection({ onDatasetClick }: Props) {
  return (
    <section id="datasets" className="relative py-24 sm:py-32">
      <div className="section-pad">
        <SectionHeading
          eyebrow="Datasets"
          title="Two Datasets. One Intelligent Analysis Pipeline."
          description="DEAP benchmark and self-collected 15-participant data feed into a unified processing pipeline. Click any dataset card to jump directly to per-model experimental results."
          align="center"
        />

        <div className="mt-16 space-y-8">
          {datasets.map((ds, i) => (
            <DatasetRow key={ds.id} ds={ds} index={i} onDatasetClick={onDatasetClick} />
          ))}
        </div>
      </div>
    </section>
  );
}

function DatasetRow({ ds, index, onDatasetClick }: {
  ds: Dataset;
  index: number;
  onDatasetClick: (dataset: 'deap' | 'custom', modelTab: string) => void;
}) {
  const a = accentMap[ds.accent];
  const reversed = index % 2 === 1;
  const isClickable = ds.id === 'deap' || ds.id === 'custom';
  const datasetKey = ds.id as 'deap' | 'custom';

  const content = (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.6 }}
      className={`grid items-center gap-6 lg:grid-cols-2 ${reversed ? 'lg:[&>*:first-child]:order-2' : ''}`}
    >
      {/* info card */}
      <div
        className={`glass relative overflow-hidden rounded-2xl p-7 transition-all duration-500 ${
          isClickable
            ? 'group cursor-pointer hover:-translate-y-0.5 hover:border-signal-400/40 hover:shadow-[0_0_60px_-20px_rgba(72,120,255,0.35)]'
            : ''
        }`}
      >
        <div className="pointer-events-none absolute right-0 top-0 h-40 w-40 rounded-full bg-signal-500/5 blur-3xl transition-opacity group-hover:opacity-100" />
        <div className="flex items-center gap-3">
          <span className={`flex h-12 w-12 items-center justify-center rounded-xl border ${a.border} ${a.bg} font-mono text-lg font-semibold ${a.text}`}>
            {ds.number}
          </span>
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-white">
              {ds.name}
              {isClickable && (
                <span className={`ml-2 inline-flex items-center gap-1 align-middle rounded-full border ${a.border} ${a.bg} px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider ${a.text} opacity-0 transition-opacity group-hover:opacity-100`}>
                  <Sparkles className="h-3 w-3" /> View Results
                </span>
              )}
            </h3>
            <p className={`font-mono text-xs uppercase tracking-wider ${a.text}`}>{ds.signalType}</p>
          </div>
        </div>

        <p className="mt-5 text-sm leading-relaxed text-slate-400">{ds.description}</p>

        {/* details grid */}
        <dl className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
          {ds.details.map((d) => (
            <div key={d.label} className="rounded-lg border border-white/5 bg-ink-950/40 px-4 py-3">
              <dt className="text-xs text-slate-500">{d.label}</dt>
              <dd className="mt-1 text-sm font-medium text-slate-200">{d.value}</dd>
            </div>
          ))}
        </dl>

        {/* pipeline mini */}
        <div className="mt-6">
          <p className="mb-3 flex items-center gap-2 font-mono text-xs uppercase tracking-wider text-slate-500">
            <GitBranch className="h-3.5 w-3.5" /> Processing Pipeline
          </p>
          <div className="flex flex-wrap items-center gap-1.5">
            {ds.pipeline.map((step, idx) => (
              <span key={step} className="flex items-center gap-1.5">
                <span className={`rounded-md border ${a.border} ${a.bg} px-2.5 py-1 text-xs ${a.text}`}>{step}</span>
                {idx < ds.pipeline.length - 1 && <span className="text-slate-600">→</span>}
              </span>
            ))}
          </div>
        </div>

        {isClickable && (
          <div className={`mt-6 inline-flex items-center gap-2 rounded-lg border ${a.border} ${a.bg} px-3 py-2 text-sm font-medium ${a.text} transition-all group-hover:translate-x-1`}>
            Jump to model results
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </div>
        )}
      </div>

      {/* visualization */}
      <div className={`glass-strong relative overflow-hidden rounded-2xl ${isClickable ? 'group/card' : ''}`}>
        <div className="flex items-center justify-between border-b border-signal-400/10 px-4 py-3">
          <span className="flex items-center gap-2 font-mono text-xs text-slate-400">
            <Database className="h-3.5 w-3.5" /> {ds.name}
          </span>
          <span className={`flex items-center gap-1.5 font-mono text-xs ${a.text}`}>
            <span className={`h-1.5 w-1.5 rounded-full ${a.dot} animate-pulse-soft`} /> active
          </span>
        </div>

        {ds.signalType === 'ECG' && (
          <div className="p-4">
            <div className="mb-2 font-mono text-xs text-slate-500">ECG waveform</div>
            <ECGWave className="h-40 w-full" color={a.wave} speed={2} />
          </div>
        )}

        {ds.signalType === 'EEG' && (
          <div className="p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="font-mono text-xs text-slate-500">32-channel EEG</span>
              <span className="font-mono text-xs text-bio-300/60">Fp1 · Fp2 · F3 · ... · Oz</span>
            </div>
            <EEGWave channels={12} className="h-56 w-full" color={a.wave} speed={1.5} />
            <ElectrodeLayout />
          </div>
        )}

        {ds.signalType === 'Other' && (
          <div className="p-4">
            <div className="mb-2 font-mono text-xs text-slate-500">Signal preview</div>
            <ECGWave className="h-40 w-full" color={a.wave} speed={1} amplitude={0.4} />
            <div className="mt-3 flex items-center gap-2 rounded-lg border border-violet-400/20 bg-violet-500/5 px-3 py-2 text-xs text-violet-200/70">
              <Cpu className="h-3.5 w-3.5" /> Dataset details editable in config
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );

  if (!isClickable) return content;
  return (
    <div
      onClick={() => onDatasetClick(datasetKey, 'svm')}
      className="focus:outline-none"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter') onDatasetClick(datasetKey, 'svm'); }}
    >
      {content}
    </div>
  );
}

function ElectrodeLayout() {
  // simplified 10-20 layout positions on a head circle
  const electrodes = [
    { x: 50, y: 12, label: 'Fp1' }, { x: 58, y: 14, label: 'Fp2' },
    { x: 35, y: 30, label: 'F7' }, { x: 45, y: 26, label: 'F3' },
    { x: 55, y: 26, label: 'F4' }, { x: 65, y: 30, label: 'F8' },
    { x: 30, y: 50, label: 'T3' }, { x: 42, y: 45, label: 'C3' },
    { x: 50, y: 44, label: 'Cz' }, { x: 58, y: 45, label: 'C4' },
    { x: 70, y: 50, label: 'T4' },
    { x: 35, y: 68, label: 'T5' }, { x: 45, y: 64, label: 'P3' },
    { x: 55, y: 64, label: 'P4' }, { x: 65, y: 68, label: 'T6' },
    { x: 50, y: 78, label: 'O1' },
  ];
  return (
    <div className="mt-4 flex items-center gap-4 rounded-lg border border-white/5 bg-ink-950/40 p-4">
      <svg viewBox="0 0 100 90" className="h-24 w-24 shrink-0">
        <ellipse cx="50" cy="45" rx="36" ry="40" fill="none" stroke="rgba(56,189,248,0.15)" strokeWidth="0.5" />
        {electrodes.map((e, i) => (
          <circle
            key={e.label}
            cx={e.x}
            cy={e.y}
            r="2"
            fill="rgba(56,189,248,0.7)"
            style={{ animation: `node-pulse ${2 + (i % 4)}s ease-in-out ${i * 0.2}s infinite` }}
          />
        ))}
      </svg>
      <div className="grid grid-cols-4 gap-x-3 gap-y-1 font-mono text-[0.6rem] text-slate-500">
        {Array.from({ length: 32 }, (_, i) => (
          <span key={i} className="text-bio-300/50">Ch{i + 1 < 10 ? '0' : ''}{i + 1}</span>
        ))}
      </div>
    </div>
  );
}
