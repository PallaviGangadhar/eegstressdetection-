import { motion } from 'framer-motion';
import { BrainCircuit, Layers, GitBranch, CheckCircle2, TestTube2, Gauge } from 'lucide-react';
import SectionHeading from '@/components/primitives/SectionHeading';
import { mlWorkflow, models } from '@/data/config';

const icons = [Layers, GitBranch, BrainCircuit, CheckCircle2, TestTube2, Gauge];

export default function ModelSection() {
  return (
    <section id="models" className="relative py-24 sm:py-32">
      <div className="section-pad">
        <SectionHeading
          eyebrow="Machine Learning"
          title="From Signal to Intelligence"
          description="The machine-learning workflow transforms processed signals into predictive models through a structured sequence of engineering, training, and validation steps."
          align="center"
        />

        {/* workflow cards */}
        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {mlWorkflow.map((w, i) => {
            const Icon = icons[i];
            return (
              <motion.div
                key={w.title}
                initial={{ opacity: 0, y: 25 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ duration: 0.45, delay: i * 0.08 }}
                className="group glass relative overflow-hidden rounded-xl p-5 transition-all duration-300 hover:-translate-y-1 hover:border-signal-400/25"
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-signal-400/20 bg-signal-500/10 text-signal-300">
                    <Icon className="h-4.5 w-4.5" strokeWidth={1.5} />
                  </span>
                  <span className="font-mono text-xs text-slate-500">STEP {String(i + 1).padStart(2, '0')}</span>
                </div>
                <h3 className="mt-4 text-base font-semibold text-white">{w.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">{w.detail}</p>
              </motion.div>
            );
          })}
        </div>

        {/* neural network visualization */}
        <div className="mt-16">
          <NeuralNetwork />
        </div>

        {/* model cards */}
        <div className="mt-16 grid gap-5 md:grid-cols-3">
          {models.map((m, i) => (
            <motion.div
              key={m.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
              className="group glass relative overflow-hidden rounded-xl p-6 text-center transition-all duration-300 hover:border-violet-400/25"
            >
              <div className="pointer-events-none absolute inset-x-0 -top-12 mx-auto h-24 w-24 rounded-full bg-violet-500/10 blur-2xl transition-opacity duration-500 group-hover:opacity-100 opacity-0" />
              <span className="font-mono text-xs uppercase tracking-widest text-violet-300/60">Model {String(i + 1).padStart(2, '0')}</span>
              <h3 className="mt-3 text-lg font-semibold text-white">{m.name}</h3>
              <p className="mt-2 text-sm text-slate-400">Dataset: <span className="text-slate-200">{m.dataset}</span></p>
              <div className="mt-4 flex justify-center gap-1.5">
                {[0, 1, 2].map((d) => (
                  <span
                    key={d}
                    className="h-1.5 w-6 rounded-full bg-violet-400/30"
                    style={{ animation: `pulse-soft ${2 + d}s ease-in-out ${d * 0.3}s infinite` }}
                  />
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function NeuralNetwork() {
  const layers = [5, 7, 7, 5, 3];
  const layerX = [60, 220, 380, 540, 700];
  const nodes: { x: number; y: number; layer: number }[] = [];
  layers.forEach((count, li) => {
    for (let i = 0; i < count; i++) {
      const spacing = 200 / (count + 1);
      nodes.push({ x: layerX[li], y: 20 + spacing * (i + 1), layer: li });
    }
  });

  return (
    <div className="glass-strong relative overflow-hidden rounded-2xl p-6">
      <div className="mb-4 flex items-center justify-between">
        <span className="font-mono text-xs uppercase tracking-widest text-slate-400">Neural Network Architecture</span>
        <span className="font-mono text-xs text-signal-300/50">interactive</span>
      </div>
      <svg viewBox="0 0 760 240" className="w-full" fill="none">
        {/* connections */}
        {nodes.map((n, i) =>
          nodes
            .filter((m) => m.layer === n.layer + 1)
            .map((m, j) => (
              <line
                key={`${i}-${j}`}
                x1={n.x}
                y1={n.y}
                x2={m.x}
                y2={m.y}
                stroke="rgba(124,165,255,0.12)"
                strokeWidth="0.6"
              />
            )),
        )}
        {/* moving particles on connections */}
        {[0, 1, 2, 3, 4, 5].map((k) => {
          const fromLayer = k % 4;
          const fromNodes = nodes.filter((n) => n.layer === fromLayer);
          const toNodes = nodes.filter((n) => n.layer === fromLayer + 1);
          const from = fromNodes[k % fromNodes.length];
          const to = toNodes[k % toNodes.length];
          if (!from || !to) return null;
          return (
            <motion.circle
              key={`p-${k}`}
              r="2"
              fill="rgba(124,165,255,0.9)"
              initial={{ cx: from.x, cy: from.y }}
              animate={{ cx: [from.x, to.x], cy: [from.y, to.y] }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                delay: k * 0.4,
                ease: 'easeInOut',
              }}
            />
          );
        })}
        {/* nodes */}
        {nodes.map((n, i) => (
          <circle
            key={i}
            cx={n.x}
            cy={n.y}
            r="4"
            fill="rgba(72,120,255,0.25)"
            stroke="rgba(124,165,255,0.5)"
            strokeWidth="1"
            style={{ animation: `node-pulse ${2 + (i % 4)}s ease-in-out ${i * 0.1}s infinite` }}
          />
        ))}
        {/* layer labels */}
        {['Input', 'Hidden 1', 'Hidden 2', 'Hidden 3', 'Output'].map((label, i) => (
          <text
            key={label}
            x={layerX[i]}
            y={232}
            textAnchor="middle"
            className="fill-slate-500 font-mono"
            fontSize="10"
          >
            {label}
          </text>
        ))}
      </svg>
    </div>
  );
}
