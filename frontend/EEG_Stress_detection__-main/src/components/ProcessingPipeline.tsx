import { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowDown } from 'lucide-react';
import SectionHeading from '@/components/primitives/SectionHeading';
import { pipelineStages } from '@/data/config';

export default function ProcessingPipeline() {
  const [hovered, setHovered] = useState<number | null>(null);

  return (
    <section id="methodology" className="relative py-24 sm:py-32">
      <div className="section-pad">
        <SectionHeading
          eyebrow="Methodology"
          title="Signal Processing Pipeline"
          description="From raw physiological signal to prediction — each stage refines the data, flowing through a sequence of deterministic steps before reaching the model."
          align="center"
        />

        <div className="mx-auto mt-16 max-w-4xl">
          <div className="flex flex-col items-stretch gap-0">
            {pipelineStages.map((stage, i) => (
              <div key={stage.id}>
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: '-40px' }}
                  transition={{ duration: 0.4, delay: i * 0.06 }}
                  onMouseEnter={() => setHovered(i)}
                  onMouseLeave={() => setHovered(null)}
                  className="group relative flex items-center gap-5 rounded-xl border border-signal-400/10 bg-ink-900/40 px-5 py-4 transition-all duration-300 hover:border-signal-400/30 hover:bg-signal-500/5"
                  data-cursor="glow"
                >
                  {/* node */}
                  <div className="relative flex shrink-0 items-center justify-center">
                    <span
                      className={`flex h-10 w-10 items-center justify-center rounded-full border font-mono text-sm transition-all duration-300 ${
                        hovered === i
                          ? 'border-signal-400 bg-signal-500/20 text-white shadow-[0_0_20px_rgba(72,120,255,0.4)]'
                          : 'border-signal-400/20 bg-ink-800 text-signal-300/70'
                      }`}
                    >
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    {hovered === i && (
                      <span className="absolute inset-0 rounded-full bg-signal-400/20 blur-md" />
                    )}
                  </div>

                  {/* label */}
                  <div className="flex-1">
                    <h3 className="text-base font-medium text-white">{stage.label}</h3>
                    <p className="text-xs text-slate-500">{stage.detail}</p>
                  </div>

                  {/* light indicator */}
                  <span
                    className={`h-1.5 w-12 rounded-full transition-all duration-300 ${
                      hovered === i ? 'bg-signal-400 shadow-[0_0_8px_rgba(72,120,255,0.6)]' : 'bg-signal-400/15'
                    }`}
                  />
                </motion.div>

                {/* connector with animated spark */}
                {i < pipelineStages.length - 1 && (
                  <div className="relative flex justify-center py-1.5">
                    <div className="relative h-8 w-px bg-gradient-to-b from-signal-400/20 to-signal-400/5">
                      <motion.span
                        className="absolute left-1/2 h-2 w-2 -translate-x-1/2 rounded-full bg-signal-300 shadow-[0_0_6px_2px_rgba(124,165,255,0.7)]"
                        animate={{ top: ['0%', '100%'] }}
                        transition={{
                          duration: 1.8,
                          repeat: Infinity,
                          delay: i * 0.3,
                          ease: 'easeInOut',
                        }}
                      />
                    </div>
                    <ArrowDown className="absolute bottom-0 h-3 w-3 text-signal-400/30" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
