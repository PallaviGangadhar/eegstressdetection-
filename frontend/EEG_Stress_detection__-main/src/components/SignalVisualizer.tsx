import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import SectionHeading from '@/components/primitives/SectionHeading';
import ECGWave from '@/components/primitives/ECGWave';
import EEGWave from '@/components/primitives/EEGWave';

const tabs = [
  { id: 'deap', label: 'DEAP EEG' },
  { id: 'custom', label: 'Custom 15-Subject' },
] as const;

type TabId = (typeof tabs)[number]['id'];

export default function SignalVisualizer() {
  const [active, setActive] = useState<TabId>('deap');

  return (
    <section id="signals" className="relative py-24 sm:py-32">
      <div className="section-pad">
        <SectionHeading
          eyebrow="Interactive Visualization"
          title="Signals Tell the Story"
          description="Switch between the DEAP benchmark dataset and your custom 15-subject collected data to explore distinct EEG patterns. Waveforms animate in real time, simulating a live biomedical monitor."
          align="center"
        />

        {/* tabs */}
        <div className="mt-10 flex justify-center">
          <div className="inline-flex rounded-full border border-signal-400/20 bg-ink-900/60 p-1">
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setActive(t.id)}
                className={`relative rounded-full px-5 py-2 text-sm font-medium transition-colors duration-300 ${
                  active === t.id ? 'text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {active === t.id && (
                  <motion.span
                    layoutId="viz-tab"
                    className="absolute inset-0 rounded-full bg-gradient-to-r from-signal-500/30 to-violet-500/20 border border-signal-400/30"
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
                <span className="relative z-10">{t.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* visualization area */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="glass-strong mx-auto mt-8 max-w-5xl overflow-hidden rounded-2xl"
        >
          {/* monitor header */}
          <div className="flex items-center justify-between border-b border-signal-400/10 px-5 py-3">
            <div className="flex items-center gap-3">
              <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse-soft" />
              <span className="font-mono text-xs text-slate-400">
                {active === 'deap' && 'DEAP_MONITOR · 32-channel EEG'}
                {active === 'custom' && 'CUSTOM_MONITOR · 15-Subject EEG'}
              </span>
            </div>
            <div className="flex gap-4 font-mono text-xs text-slate-500">
              <span>250 Hz</span>
              <span>16-bit</span>
              <span className="text-emerald-400/60">REC</span>
            </div>
          </div>

          <div className="relative h-[420px] sm:h-[480px]">
            <AnimatePresence mode="wait">
              {active === 'deap' && (
                <motion.div
                  key="deap"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 p-5"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span className="font-mono text-xs text-bio-300/60">DEAP · 32-channel EEG · Benchmark dataset</span>
                  </div>
                  <div className="grid h-[calc(100%-1.5rem)] grid-cols-1 gap-x-4 sm:grid-cols-2">
                    <div className="relative">
                      <EEGWave channels={16} className="h-full w-full" color="#38bdf8" speed={1.5} />
                    </div>
                    <div className="relative hidden sm:block">
                      <EEGWave channels={16} className="h-full w-full" color="#7ca5ff" speed={1.3} />
                    </div>
                  </div>
                  <div className="pointer-events-none absolute left-5 top-9 space-y-[18px] font-mono text-[0.6rem] text-bio-300/40">
                    {Array.from({ length: 16 }, (_, i) => (
                      <div key={i}>Ch{i + 1 < 10 ? '0' : ''}{i + 1}</div>
                    ))}
                  </div>
                </motion.div>
              )}
              {active === 'custom' && (
                <motion.div
                  key="custom"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 p-5"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span className="font-mono text-xs text-signal-300/60">Custom Collected · 15-Subject EEG · XDF format</span>
                  </div>
                  <div className="grid h-[calc(100%-1.5rem)] grid-cols-1 gap-x-4 sm:grid-cols-2">
                    <div className="relative">
                      <EEGWave channels={12} className="h-full w-full" color="#4878ff" speed={1.4} />
                    </div>
                    <div className="relative hidden sm:block">
                      <EEGWave channels={12} className="h-full w-full" color="#60a5fa" speed={1.2} />
                    </div>
                  </div>
                  <div className="pointer-events-none absolute left-5 top-9 space-y-[22px] font-mono text-[0.6rem] text-signal-300/40">
                    {Array.from({ length: 12 }, (_, i) => (
                      <div key={i}>Ch{i + 1 < 10 ? '0' : ''}{i + 1}</div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
