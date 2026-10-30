import { motion } from 'framer-motion';
import SectionHeading from '@/components/primitives/SectionHeading';
import { timeline } from '@/data/config';

export default function Timeline() {
  return (
    <section className="relative py-24 sm:py-32">
      <div className="section-pad">
        <SectionHeading
          eyebrow="Research Timeline"
          title="From Data to Discovery"
          description="The research journey, from dataset collection to final analysis — each phase building on the last."
          align="center"
        />

        <div className="mx-auto mt-16 max-w-3xl">
          {/* vertical line */}
          <div className="relative">
            <div className="absolute left-4 top-0 h-full w-px bg-gradient-to-b from-signal-400/40 via-signal-400/15 to-transparent sm:left-1/2 sm:-translate-x-1/2" />

            {timeline.map((item, i) => {
              const left = i % 2 === 0;
              return (
                <motion.div
                  key={item.phase}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-50px' }}
                  transition={{ duration: 0.5, delay: i * 0.06 }}
                  className={`relative flex items-start gap-6 pb-10 sm:gap-0 ${
                    left ? 'sm:flex-row' : 'sm:flex-row-reverse'
                  }`}
                >
                  {/* node */}
                  <div className="absolute left-4 top-1 z-10 -translate-x-1/2 sm:left-1/2">
                    <span className="flex h-3 w-3 rounded-full bg-signal-400 shadow-[0_0_10px_2px_rgba(72,120,255,0.5)]" />
                    <span className="absolute inset-0 animate-ping rounded-full bg-signal-400/40" />
                  </div>

                  {/* content */}
                  <div className={`ml-10 flex-1 sm:ml-0 sm:w-1/2 ${left ? 'sm:pr-12 sm:text-right' : 'sm:pl-12'}`}>
                    <div className="glass rounded-xl p-5 transition-all duration-300 hover:border-signal-400/25">
                      <span className="font-mono text-xs text-signal-300/60">PHASE {item.phase}</span>
                      <h3 className="mt-2 text-base font-semibold text-white">{item.title}</h3>
                      <p className="mt-2 text-sm leading-relaxed text-slate-400">{item.detail}</p>
                    </div>
                  </div>
                  {/* spacer for the other side on desktop */}
                  <div className="hidden sm:block sm:w-1/2" />
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
