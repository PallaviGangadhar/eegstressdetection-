import { motion } from 'framer-motion';
import SectionHeading from '@/components/primitives/SectionHeading';
import { architectureStages } from '@/data/config';

export default function ArchitectureDiagram() {
  return (
    <section className="relative py-24 sm:py-32">
      <div className="section-pad">
        <SectionHeading
          eyebrow="System Architecture"
          title="Research Architecture"
          description="The complete pipeline from raw datasets to final prediction, visualised as a flowing scientific system diagram."
          align="center"
        />

        <div className="mx-auto mt-16 max-w-3xl">
          {/* vertical flow with animated traveling particles */}
          <div className="relative">
            {architectureStages.map((stage, i) => (
              <motion.div
                key={stage}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-30px' }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="relative flex items-center"
              >
                {/* connecting line with particle */}
                {i > 0 && (
                  <div className="absolute left-1/2 -top-6 h-6 w-px -translate-x-1/2 bg-gradient-to-b from-signal-400/30 to-signal-400/10">
                    <motion.span
                      className="absolute left-1/2 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-signal-300 shadow-[0_0_6px_2px_rgba(124,165,255,0.7)]"
                      animate={{ top: ['-10%', '110%'] }}
                      transition={{
                        duration: 1.6,
                        repeat: Infinity,
                        delay: i * 0.25,
                        ease: 'easeIn',
                      }}
                    />
                  </div>
                )}

                <div className="group relative mx-auto flex w-full max-w-md items-center gap-4 overflow-hidden rounded-xl border border-signal-400/15 bg-ink-900/50 px-5 py-4 transition-all duration-300 hover:border-signal-400/35 hover:bg-signal-500/5">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-signal-400/25 bg-signal-500/10 font-mono text-xs text-signal-300">
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span className="flex-1 text-sm font-medium text-white">{stage}</span>
                  {/* progress bar */}
                  <span className="h-1 w-12 rounded-full bg-signal-400/20">
                    <span
                      className="block h-full rounded-full bg-gradient-to-r from-signal-400 to-violet-400"
                      style={{ width: `${((i + 1) / architectureStages.length) * 100}%` }}
                    />
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
