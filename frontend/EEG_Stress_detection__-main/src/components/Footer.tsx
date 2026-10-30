import { Activity } from 'lucide-react';

const footerLinks = [
  { label: 'Home', href: '#home' },
  { label: 'Research', href: '#research' },
  { label: 'Datasets', href: '#datasets' },
  { label: 'Methodology', href: '#methodology' },
  { label: 'Models', href: '#models' },
  { label: 'Results', href: '#results' },
  { label: 'About', href: '#about' },
  { label: 'Contact', href: '#contact' },
];

export default function Footer() {
  return (
    <footer className="relative border-t border-signal-400/10 py-12">
      <div className="section-pad">
        <div className="flex flex-col items-center gap-6 text-center">
          <a href="#home" className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-signal-400/30 bg-signal-500/10">
              <Activity className="h-4.5 w-4.5 text-signal-300" strokeWidth={2} />
            </span>
            <span className="font-semibold tracking-tight text-white">
              NeuroSignal<span className="text-signal-400"> AI</span>
            </span>
          </a>

          <p className="font-mono text-xs uppercase tracking-[0.25em] text-slate-500">
            ECG · EEG · Signal Processing · Artificial Intelligence
          </p>

          <nav className="flex flex-wrap justify-center gap-x-5 gap-y-2">
            {footerLinks.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="text-sm text-slate-400 transition-colors hover:text-signal-300"
              >
                {l.label}
              </a>
            ))}
          </nav>

          <div className="h-px w-24 bg-gradient-to-r from-transparent via-signal-400/30 to-transparent" />

          <p className="text-xs text-slate-600">
            AI Biomedical Signal Analysis — Research Platform · {new Date().getFullYear()}
          </p>
        </div>
      </div>
    </footer>
  );
}
