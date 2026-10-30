import { useRef, useState, type ReactNode, type MouseEvent } from 'react';
import { ArrowRight } from 'lucide-react';

type Props = {
  children: ReactNode;
  href?: string;
  onClick?: () => void;
  className?: string;
  arrowClassName?: string;
  variant?: 'link' | 'button';
};

/**
 * Arrow with a spark particle that travels along it on hover.
 * Occasionally a spark auto-fires at random intervals to feel alive.
 */
export default function SparkArrow({
  children,
  href,
  onClick,
  className = '',
  arrowClassName = '',
  variant = 'link',
}: Props) {
  const [sparks, setSparks] = useState<number[]>([]);
  const idRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fireSpark = () => {
    const id = idRef.current++;
    setSparks((s) => [...s, id]);
    setTimeout(() => setSparks((s) => s.filter((x) => x !== id)), 1200);
  };

  const handleEnter = () => {
    fireSpark();
    // random occasional sparks while hovering
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      if (Math.random() > 0.6) fireSpark();
    }, 1400);
  };

  const handleLeave = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const handleClick = (e: MouseEvent) => {
    if (onClick) {
      e.preventDefault();
      onClick();
    }
  };

  const base =
    variant === 'button'
      ? 'group relative inline-flex items-center gap-2.5 px-6 py-3 rounded-full font-medium text-sm transition-all duration-300 '
      : 'group relative inline-flex items-center gap-2 font-medium text-sm transition-colors duration-300 ';

  return (
    <a
      href={href || '#'}
      onClick={handleClick}
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
      className={`${base} ${className}`}
    >
      <span className="relative z-10">{children}</span>
      <span className={`relative z-10 inline-flex items-center ${arrowClassName}`}>
        <span className="relative inline-block w-5 overflow-hidden">
          {/* the arrow */}
          <ArrowRight
            className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-0.5"
            strokeWidth={1.75}
          />
          {/* spark track */}
          <span className="pointer-events-none absolute inset-0 overflow-hidden">
            {sparks.map((id) => (
              <span
                key={id}
                className="spark-run absolute top-1/2 h-[2px] w-2 -translate-y-1/2 rounded-full bg-signal-300 shadow-[0_0_8px_2px_rgba(124,165,255,0.8)]"
                style={{ left: '-10%' }}
              />
            ))}
          </span>
        </span>
      </span>
    </a>
  );
}
