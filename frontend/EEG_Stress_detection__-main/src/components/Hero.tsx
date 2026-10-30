import { motion } from 'framer-motion';
import { Activity, Brain, Zap } from 'lucide-react';
import SparkArrow from '@/components/primitives/SparkArrow';
import ECGWave from '@/components/primitives/ECGWave';
import EEGWave from '@/components/primitives/EEGWave';

export default function Hero() {
  return (
    <section
      id="home"
      className="relative flex min-h-screen items-center overflow-hidden pt-28 pb-16"
    >
      {/* radial glow behind hero */}
      <div className="pointer-events-none absolute left-1/2 top-1/3 -z-10 h-[600px] w-[600px] -translate-x-1/2 rounded-full bg-signal-500/10 blur-[120px]" />

      <div className="section-pad grid w-full items-center gap-12 lg:grid-cols-[1.1fr_0.9fr]">
        {/* Left — content */}
        <div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 rounded-full border border-signal-400/20 bg-signal-500/5 px-4 py-1.5"
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal-400 opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-signal-400" />
            </span>
            <span className="font-mono text-xs tracking-widest text-signal-200/80">
              RESEARCH PLATFORM · LIVE
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="mt-6 text-4xl font-semibold leading-[1.1] tracking-tight text-white sm:text-5xl lg:text-6xl xl:text-7xl"
          >
            AI-Driven
            <br />
            <span className="bg-gradient-to-r from-signal-300 via-signal-400 to-violet-400 bg-clip-text text-transparent glow-text">
              Biomedical Signal
            </span>
            <br />
            Analysis
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.25 }}
            className="mt-6 max-w-xl text-lg leading-relaxed text-slate-300"
          >
            Decoding physiological signals through intelligent machine learning
            and deep learning.
          </motion.p>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.35 }}
            className="mt-3 max-w-xl text-sm leading-relaxed text-slate-400"
          >
            An experimental research platform for analyzing ECG and EEG signals
            using multiple biomedical datasets, signal-processing techniques,
            and AI models.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.45 }}
            className="mt-8 flex flex-wrap items-center gap-4"
          >
            <SparkArrow
              href="#research"
              variant="button"
              className="bg-gradient-to-r from-signal-500 to-signal-600 text-white shadow-[0_0_30px_-5px_rgba(72,120,255,0.5)] hover:shadow-[0_0_40px_-2px_rgba(72,120,255,0.7)]"
            >
              Explore Research
            </SparkArrow>
            <SparkArrow
              href="#signals"
              variant="button"
              className="border border-signal-400/30 text-signal-100 hover:border-signal-400/60 hover:bg-signal-500/10"
            >
              View Signal Analysis
            </SparkArrow>
          </motion.div>

          {/* mini stats row */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="mt-12 flex gap-8"
          >
            {[
              { icon: Activity, label: 'ECG', sub: 'Cardiac signals' },
              { icon: Brain, label: 'EEG · 32ch', sub: 'Brain signals' },
              { icon: Zap, label: 'AI Models', sub: 'Deep learning' },
            ].map((s) => (
              <div key={s.label} className="flex items-center gap-2.5">
                <s.icon className="h-4 w-4 text-signal-300" strokeWidth={1.5} />
                <div>
                  <div className="text-sm font-medium text-white">{s.label}</div>
                  <div className="text-xs text-slate-500">{s.sub}</div>
                </div>
              </div>
            ))}
          </motion.div>
        </div>

        {/* Right — signal visualization */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="relative"
        >
          <div className="glass-strong relative overflow-hidden rounded-2xl p-1">
            {/* monitor header */}
            <div className="flex items-center justify-between border-b border-signal-400/10 px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-rose-400/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-amber-400/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/70" />
              </div>
              <span className="font-mono text-xs text-slate-400">
                signal_monitor.py
              </span>
            </div>

            {/* ECG panel */}
            <div className="relative">
              <div className="absolute left-3 top-3 z-10 flex items-center gap-2">
                <span className="font-mono text-[0.65rem] uppercase tracking-widest text-signal-300/70">
                  ECG · Lead II
                </span>
              </div>
              <ECGWave className="h-32 w-full" color="#4878ff" />
            </div>

            {/* divider */}
            <div className="h-px bg-signal-400/10" />

            {/* EEG panel */}
            <div className="relative">
              <div className="absolute left-3 top-3 z-10 flex items-center gap-2">
                <span className="font-mono text-[0.65rem] uppercase tracking-widest text-bio-300/70">
                  EEG · 32-channel
                </span>
              </div>
              <EEGWave channels={8} className="h-48 w-full" color="#38bdf8" />
            </div>

            {/* footer status */}
            <div className="flex items-center justify-between border-t border-signal-400/10 px-4 py-2.5">
              <span className="font-mono text-xs text-emerald-400/70">
                ● streaming
              </span>
              <span className="font-mono text-xs text-slate-500">
                250 Hz · 16-bit
              </span>
            </div>
          </div>

          {/* floating neural nodes */}
          <div className="pointer-events-none absolute -right-4 -top-4 hidden sm:block">
            <NeuralMini />
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function NeuralMini() {
  const nodes = [
    { x: 10, y: 20 }, { x: 40, y: 8 }, { x: 70, y: 24 }, { x: 90, y: 12 },
    { x: 20, y: 50 }, { x: 55, y: 44 }, { x: 82, y: 52 },
    { x: 35, y: 72 }, { x: 68, y: 76 },
  ];
  return (
    <svg width="120" height="90" viewBox="0 0 100 85" fill="none">
      {nodes.map((n, i) =>
        nodes.slice(i + 1).map((m, j) => {
          const dist = Math.hypot(n.x - m.x, n.y - m.y);
          if (dist > 40) return null;
          return (
            <line
              key={`${i}-${j}`}
              x1={n.x}
              y1={n.y}
              x2={m.x}
              y2={m.y}
              stroke="rgba(124,165,255,0.15)"
              strokeWidth="0.5"
            />
          );
        }),
      )}
      {nodes.map((n, i) => (
        <circle
          key={i}
          cx={n.x}
          cy={n.y}
          r="2"
          fill="rgba(124,165,255,0.8)"
          style={{
            animation: `node-pulse ${2 + (i % 3)}s ease-in-out ${i * 0.3}s infinite`,
          }}
        />
      ))}
    </svg>
  );
}
