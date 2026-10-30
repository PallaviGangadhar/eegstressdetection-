import { motion } from 'framer-motion';
import { Trophy } from 'lucide-react';
import SectionHeading from '@/components/primitives/SectionHeading';
import { modelComparisonRows, type Metric } from '@/data/config';

const columns: { key: keyof (typeof modelComparisonRows)[number]; label: string }[] = [
  { key: 'accuracy', label: 'Accuracy' },
  { key: 'precision', label: 'Precision' },
  { key: 'recall', label: 'Recall' },
  { key: 'f1', label: 'F1 Score' },
  { key: 'auc', label: 'AUC' },
  { key: 'trainingTime', label: 'Training Time' },
];

const fmt = (v: Metric, suffix = '') => (v === null ? '—' : `${v}${suffix}`);

export default function ModelComparison() {
  return (
    <section className="relative py-24 sm:py-32">
      <div className="section-pad">
        <SectionHeading
          eyebrow="Model Comparison"
          title="Performance Dashboard"
          description="Side-by-side comparison of models across standard classification metrics. Values display as '—' until experimental results are supplied."
          align="center"
        />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.6 }}
          className="glass-strong mx-auto mt-12 max-w-5xl overflow-hidden rounded-2xl"
        >
          <div className="overflow-x-auto">
            <table className="w-full min-w-[680px] text-left text-sm">
              <thead>
                <tr className="border-b border-signal-400/15">
                  <th className="px-5 py-4 font-mono text-xs uppercase tracking-wider text-slate-400">Model</th>
                  <th className="px-5 py-4 font-mono text-xs uppercase tracking-wider text-slate-400">Dataset</th>
                  {columns.map((c) => (
                    <th key={c.key} className="px-5 py-4 text-right font-mono text-xs uppercase tracking-wider text-slate-400">
                      {c.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {modelComparisonRows.map((row, i) => (
                  <motion.tr
                    key={row.model}
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.4, delay: i * 0.1 }}
                    className="border-b border-white/5 transition-colors hover:bg-signal-500/5"
                  >
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2.5">
                        <span className="flex h-7 w-7 items-center justify-center rounded-md border border-violet-400/20 bg-violet-500/10">
                          <Trophy className="h-3.5 w-3.5 text-violet-300" />
                        </span>
                        <span className="font-medium text-white">{row.model}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-slate-300">{row.dataset}</td>
                    {columns.map((c) => {
                      const suffix = c.key === 'accuracy' || c.key === 'trainingTime' ? '' : '';
                      return (
                        <td key={c.key} className="px-5 py-4 text-right font-mono text-slate-300">
                          {fmt(row[c.key] as Metric, suffix)}
                        </td>
                      );
                    })}
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="border-t border-signal-400/10 px-5 py-3">
            <p className="font-mono text-xs text-slate-500">
              '—' indicates values not yet available. Update in <span className="text-signal-300/60">config.ts</span>.
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
