import { motion } from 'framer-motion';
import {
  Code2, Sigma, Table2, AudioWaveform, BrainCircuit, Network,
  BarChart3, NotebookPen, type LucideIcon,
} from 'lucide-react';
import SectionHeading from '@/components/primitives/SectionHeading';
import { technologies } from '@/data/config';

const iconMap: Record<string, LucideIcon> = {
  Code2, Sigma, Table2, AudioWaveform, BrainCircuit, Network, BarChart3, NotebookPen,
};

export default function TechnologyStack() {
  return (
    <section className="relative py-24 sm:py-32">
      <div className="section-pad">
        <SectionHeading
          eyebrow="Technology Stack"
          title="Tools & Frameworks"
          description="The technologies powering the signal-processing and AI pipeline."
          align="center"
        />

        <div className="mx-auto mt-12 grid max-w-4xl grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {technologies.map((tech, i) => {
            const Icon = iconMap[tech.icon] ?? Code2;
            return (
              <motion.div
                key={tech.name}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true, margin: '-30px' }}
                transition={{ duration: 0.35, delay: i * 0.05 }}
                className="group glass flex flex-col items-center gap-3 rounded-xl p-5 text-center transition-all duration-300 hover:-translate-y-1 hover:border-signal-400/25"
              >
                <span className="flex h-12 w-12 items-center justify-center rounded-xl border border-signal-400/20 bg-signal-500/10 text-signal-300 transition-all duration-300 group-hover:shadow-[0_0_20px_rgba(72,120,255,0.3)]">
                  <Icon className="h-5 w-5" strokeWidth={1.5} />
                </span>
                <span className="text-sm font-medium text-slate-200">{tech.name}</span>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
