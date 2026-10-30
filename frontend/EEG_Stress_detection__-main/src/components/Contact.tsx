import { motion } from 'framer-motion';
import { Mail, Github, Linkedin, User, Building2, BookOpen, Link2 } from 'lucide-react';
import SectionHeading from '@/components/primitives/SectionHeading';
import { researcher } from '@/data/config';

export default function Contact() {
  return (
    <section id="contact" className="relative py-24 sm:py-32">
      <div className="section-pad">
        <SectionHeading
          eyebrow="Contact / Research Profile"
          title="Let's Explore the Signal Beneath the Surface"
          description="Connect regarding this research, collaboration opportunities, or technical details about the platform."
          align="center"
        />

        <div className="mx-auto mt-12 max-w-3xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.6 }}
            className="glass-strong relative overflow-hidden rounded-2xl p-8 sm:p-10"
          >
            <div className="pointer-events-none absolute -right-20 -top-20 h-60 w-60 rounded-full bg-signal-500/10 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-20 -left-20 h-60 w-60 rounded-full bg-violet-500/8 blur-3xl" />

            {/* researcher name */}
            <div className="flex flex-col items-center text-center">
              <span className="flex h-16 w-16 items-center justify-center rounded-full border border-signal-400/25 bg-signal-500/10">
                <User className="h-7 w-7 text-signal-300" strokeWidth={1.5} />
              </span>
              <h3 className="mt-4 text-2xl font-semibold text-white">{researcher.name}</h3>
              <p className="mt-1 text-sm text-slate-400">{researcher.department}</p>
              <p className="text-sm text-slate-500">{researcher.institution}</p>
            </div>

            {/* contact grid */}
            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              <ContactRow icon={Mail} label="Email" value={researcher.email} href={`mailto:${researcher.email}`} />
              <ContactRow icon={Building2} label="Institution" value={researcher.institution} />
              <ContactRow icon={BookOpen} label="Department" value={researcher.department} />
              <ContactRow icon={Github} label="GitHub" value={researcher.github} href={`https://github.com/${researcher.github}`} />
              <ContactRow icon={Linkedin} label="LinkedIn" value={researcher.linkedin} href={`https://linkedin.com/in/${researcher.linkedin}`} />
              <ContactRow icon={Link2} label="Repository" value={researcher.repository} href={researcher.repository} />
            </div>

            {/* CTA */}
            <div className="mt-8 flex justify-center">
              <a
                href={`mailto:${researcher.email}`}
                className="group inline-flex items-center gap-2.5 rounded-full bg-gradient-to-r from-signal-500 to-signal-600 px-7 py-3.5 text-sm font-medium text-white shadow-[0_0_30px_-5px_rgba(72,120,255,0.5)] transition-all duration-300 hover:shadow-[0_0_40px_-2px_rgba(72,120,255,0.7)]"
              >
                Start a Conversation
                <span className="transition-transform duration-300 group-hover:translate-x-0.5">→</span>
              </a>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

function ContactRow({
  icon: Icon,
  label,
  value,
  href,
}: {
  icon: typeof Mail;
  label: string;
  value: string;
  href?: string;
}) {
  const content = (
    <div className="flex items-center gap-3 rounded-xl border border-signal-400/10 bg-ink-900/40 px-4 py-3.5 transition-all duration-300 hover:border-signal-400/25 hover:bg-signal-500/5">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-signal-400/20 bg-signal-500/10 text-signal-300">
        <Icon className="h-4 w-4" strokeWidth={1.5} />
      </span>
      <div className="min-w-0">
        <p className="font-mono text-xs uppercase tracking-wider text-slate-500">{label}</p>
        <p className="truncate text-sm text-slate-200">{value}</p>
      </div>
    </div>
  );

  if (href) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className="block">
        {content}
      </a>
    );
  }
  return content;
}
