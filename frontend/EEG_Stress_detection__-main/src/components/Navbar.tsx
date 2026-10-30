import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Menu, X } from 'lucide-react';
import SparkArrow from '@/components/primitives/SparkArrow';

const links = [
  { label: 'Home', href: '#home' },
  { label: 'Research', href: '#research' },
  { label: 'Datasets', href: '#datasets' },
  { label: 'Methodology', href: '#methodology' },
  { label: 'Models', href: '#models' },
  { label: 'Results', href: '#results' },
  { label: 'About', href: '#about' },
  { label: 'Contact', href: '#contact' },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <motion.nav
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-500 ${
        scrolled
          ? 'glass-strong border-b border-signal-400/10 py-3'
          : 'bg-transparent py-5'
      }`}
    >
      <div className="section-pad flex items-center justify-between">
        <a href="#home" className="group flex items-center gap-2.5">
          <span className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-signal-400/30 bg-signal-500/10">
            <Activity className="h-4.5 w-4.5 text-signal-300" strokeWidth={2} />
            <span className="absolute inset-0 rounded-lg bg-signal-400/20 blur-md transition-opacity group-hover:opacity-100 opacity-0" />
          </span>
          <span className="font-semibold tracking-tight text-white">
            NeuroSignal<span className="text-signal-400"> AI</span>
          </span>
        </a>

        {/* Desktop links */}
        <ul className="hidden items-center gap-1 lg:flex">
          {links.map((l) => (
            <li key={l.href}>
              <a
                href={l.href}
                className="group relative px-3.5 py-2 text-sm text-slate-300 transition-colors hover:text-white"
              >
                {l.label}
                <span className="absolute inset-x-3.5 -bottom-0.5 h-px origin-left scale-x-0 bg-gradient-to-r from-signal-400 to-violet-400 transition-transform duration-300 group-hover:scale-x-100" />
              </a>
            </li>
          ))}
        </ul>

        <div className="hidden lg:block">
          <SparkArrow
            href="#contact"
            variant="button"
            className="border border-signal-400/30 text-signal-200 hover:border-signal-400/60 hover:bg-signal-500/10"
          >
            Get in Touch
          </SparkArrow>
        </div>

        {/* Mobile toggle */}
        <button
          onClick={() => setOpen((o) => !o)}
          className="flex h-10 w-10 items-center justify-center rounded-lg border border-signal-400/20 text-slate-200 lg:hidden"
          aria-label="Toggle menu"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden lg:hidden"
          >
            <ul className="section-pad flex flex-col gap-1 py-4">
              {links.map((l) => (
                <li key={l.href}>
                  <a
                    href={l.href}
                    onClick={() => setOpen(false)}
                    className="block rounded-lg px-4 py-3 text-sm text-slate-300 transition-colors hover:bg-signal-500/10 hover:text-white"
                  >
                    {l.label}
                  </a>
                </li>
              ))}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
}
