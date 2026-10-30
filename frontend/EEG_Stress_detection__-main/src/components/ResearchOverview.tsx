import { motion } from 'framer-motion';
import { Heart, Brain, Layers } from 'lucide-react';
import SectionHeading from '@/components/primitives/SectionHeading';
import ECGWave from '@/components/primitives/ECGWave';
import EEGWave from '@/components/primitives/EEGWave';
import { datasets } from '@/data/config';

const icons = [Heart, Brain, Layers];
const accentMap = {
  signal: { text: 'text-signal-300', border: 'border-signal-400/30', glow: 'bg-signal-500/10', wave: '#4878ff' },
  bio: { text: 'text-bio-300', border: 'border-bio-400/30', glow: 'bg-bio-500/10', wave: '#38bdf8' },
  violet: { text: 'text-violet-300', border: 'border-violet-400/30', glow: 'bg-violet-500/10', wave: '#a78bfa' },
} as const;

export default function ResearchOverview() {
  return (
    <section id="research" className="relative py-24 sm:py-32">
      <div className="section-pad">
        <SectionHeading
          eyebrow="Research Overview"
          title={
            <>
              Research at the Intersection of
              <br className="hidden sm:block" /> Biology and AI
            </>
          }
          description="This project investigates how machine learning and deep learning can extract meaningful information from physiological signals — turning raw biomedical data into clinical and scientific insight."
        />

        <div className="mt-14 grid gap-6 md:grid-cols-3">
          {datasets.map((ds, i) => {
            const Icon = icons[i];
            const a = accentMap[ds.accent];
            return (
              <motion.article
                key={ds.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-60px' }}
                transition={{ duration: 0.5, delay: i * 0.12 }}
                className="group glass relative overflow-hidden rounded-2xl p-6 transition-all duration-300 hover:-translate-y-1 hover:border-signal-400/25"
                data-cursor="glow"
              >
                {/* glow on hover */}
                <div className={`pointer-events-none absolute -right-12 -top-12 h-32 w-32 rounded-full ${a.glow} opacity-0 blur-3xl transition-opacity duration-500 group-hover:opacity-100`} />

                <div className="flex items-center justify-between">
                  <span className={`flex h-11 w-11 items-center justify-center rounded-xl border ${a.border} ${a.glow}`}>
                    <Icon className={`h-5 w-5 ${a.text}`} strokeWidth={1.5} />
                  </span>
                  <span className="font-mono text-xs text-slate-500">TRACK {ds.number}</span>
                </div>

                <h3 className="mt-5 text-lg font-semibold text-white">{ds.name}</h3>
                <p className={`mt-1 font-mono text-xs uppercase tracking-wider ${a.text}`}>{ds.signalType}</p>
                <p className="mt-3 text-sm leading-relaxed text-slate-400">{ds.description}</p>

                {/* waveform preview */}
                <div className="mt-5 overflow-hidden rounded-lg border border-white/5 bg-ink-950/50">
                  {ds.signalType === 'ECG' ? (
                    <ECGWave className="h-16 w-full" color={a.wave} speed={1.5} />
                  ) : ds.signalType === 'EEG' ? (
                    <EEGWave channels={4} className="h-16 w-full" color={a.wave} speed={1.2} />
                  ) : (
                    <ECGWave className="h-16 w-full" color={a.wave} speed={1} amplitude={0.5} />
                  )}
                </div>

                <dl className="mt-5 space-y-2 text-xs">
                  <div className="flex justify-between gap-2">
                    <dt className="text-slate-500">Purpose</dt>
                    <dd className="text-right text-slate-300">{ds.purpose}</dd>
                  </div>
                  <div className="flex justify-between gap-2">
                    <dt className="text-slate-500">Approach</dt>
                    <dd className="text-right text-slate-300">{ds.approach}</dd>
                  </div>
                </dl>
              </motion.article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
