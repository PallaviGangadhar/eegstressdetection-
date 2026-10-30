import { motion } from 'framer-motion';
import { Database, Brain, CheckCircle2 } from 'lucide-react';
import SectionHeading from '@/components/primitives/SectionHeading';
import { philosophy } from '@/data/config';

const icons = [Database, Brain, CheckCircle2];

export default function About() {
  return (
    <>
      {/* About section */}
      <section id="about" className="relative py-24 sm:py-32">
        <div className="section-pad">
          <div className="mx-auto max-w-3xl">
            <SectionHeading
              eyebrow="About the Project"
              title="Exploring the Signal Beneath the Surface"
            />
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.6 }}
              className="mt-8 space-y-5 text-base leading-relaxed text-slate-300"
            >
              <p>
                The goal of this project is to explore how computational
                intelligence can transform complex physiological signals into
                meaningful information. By combining biomedical signal
                processing with machine learning and deep learning, the project
                investigates patterns hidden within ECG and EEG recordings.
              </p>
              <p>
                Rather than treating signals as mere data points, the research
                approach emphasises understanding the underlying physiology —
                the cardiac electrical cascade, the cortical rhythm patterns —
                before applying intelligent models. This ensures the AI is
                guided by domain knowledge rather than relying on pattern
                matching alone.
              </p>
              <p>
                The platform serves as both a research portfolio and a
                demonstration of how modern AI can be applied responsibly to
                biomedical signal analysis, with rigorous validation at every
                stage of the pipeline.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Research philosophy */}
      <section className="relative py-24 sm:py-32">
        <div className="section-pad">
          <SectionHeading
            eyebrow="Research Philosophy"
            title="Three Principles"
            align="center"
          />
          <div className="mx-auto mt-14 grid max-w-4xl gap-6 sm:grid-cols-3">
            {philosophy.map((p, i) => {
              const Icon = icons[i];
              return (
                <motion.div
                  key={p.title}
                  initial={{ opacity: 0, y: 25 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-40px' }}
                  transition={{ duration: 0.5, delay: i * 0.1 }}
                  className="group glass relative flex flex-col items-center overflow-hidden rounded-2xl p-8 text-center transition-all duration-300 hover:-translate-y-1 hover:border-signal-400/25"
                >
                  <div className="pointer-events-none absolute inset-x-0 -top-10 mx-auto h-20 w-20 rounded-full bg-signal-500/10 blur-2xl opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
                  {/* glowing node */}
                  <span className="relative flex h-16 w-16 items-center justify-center rounded-full border border-signal-400/25 bg-signal-500/10">
                    <Icon className="h-6 w-6 text-signal-300" strokeWidth={1.5} />
                    <span className="absolute inset-0 rounded-full bg-signal-400/15 animate-pulse-soft" />
                  </span>
                  <h3 className="mt-5 text-lg font-semibold text-white">{p.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-slate-400">{p.text}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>
    </>
  );
}
