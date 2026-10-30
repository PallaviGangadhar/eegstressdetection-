import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

type Props = {
  eyebrow: string;
  title: ReactNode;
  description?: string;
  align?: 'left' | 'center';
};

export default function SectionHeading({
  eyebrow,
  title,
  description,
  align = 'left',
}: Props) {
  return (
    <div className={align === 'center' ? 'text-center mx-auto max-w-3xl' : 'max-w-3xl'}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-80px' }}
        transition={{ duration: 0.6 }}
      >
        <div className={`flex items-center gap-3 ${align === 'center' ? 'justify-center' : ''}`}>
          <span className="h-px w-8 bg-gradient-to-r from-transparent to-signal-400/60" />
          <span className="eyebrow">{eyebrow}</span>
          <span className="h-px w-8 bg-gradient-to-l from-transparent to-signal-400/60" />
        </div>
        <h2 className="mt-4 text-3xl font-semibold leading-tight text-white sm:text-4xl lg:text-5xl">
          {title}
        </h2>
        {description && (
          <p className="mt-4 text-base leading-relaxed text-slate-400 sm:text-lg">
            {description}
          </p>
        )}
      </motion.div>
    </div>
  );
}
