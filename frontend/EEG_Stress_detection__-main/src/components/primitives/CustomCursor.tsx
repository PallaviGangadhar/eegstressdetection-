import { useEffect, useRef } from 'react';
import { useReducedMotion } from '@/hooks/useMotion';

/**
 * Subtle custom cursor glow — a trailing soft dot that follows the pointer.
 * Disabled on touch / coarse pointers and when reduced motion is requested.
 */
export default function CustomCursor() {
  const dotRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const reduced = useReducedMotion();

  useEffect(() => {
    if (reduced) return;
    const fine = window.matchMedia('(pointer: fine)').matches;
    if (!fine) return;

    const dot = dotRef.current;
    const ring = ringRef.current;
    if (!dot || !ring) return;

    let mx = window.innerWidth / 2;
    let my = window.innerHeight / 2;
    let rx = mx;
    let ry = my;
    let raf = 0;
    let visible = false;

    const onMove = (e: MouseEvent) => {
      mx = e.clientX;
      my = e.clientY;
      dot.style.transform = `translate(${mx}px, ${my}px)`;
      if (!visible) {
        visible = true;
        dot.style.opacity = '1';
        ring.style.opacity = '1';
      }

      const target = e.target as HTMLElement;
      const interactive = target.closest('a, button, [data-cursor="glow"]');
      ring.classList.toggle('cursor-active', !!interactive);
    };

    const onLeave = () => {
      dot.style.opacity = '0';
      ring.style.opacity = '0';
      visible = false;
    };

    const animate = () => {
      rx += (mx - rx) * 0.15;
      ry += (my - ry) * 0.15;
      ring.style.transform = `translate(${rx}px, ${ry}px)`;
      raf = requestAnimationFrame(animate);
    };
    animate();

    document.body.classList.add('cursor-glow-active');
    window.addEventListener('mousemove', onMove);
    document.addEventListener('mouseleave', onLeave);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseleave', onLeave);
      document.body.classList.remove('cursor-glow-active');
    };
  }, [reduced]);

  if (reduced) return null;

  return (
    <>
      <div
        ref={dotRef}
        className="pointer-events-none fixed left-0 top-0 z-[9999] h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-signal-300 opacity-0 transition-opacity duration-300"
        style={{ boxShadow: '0 0 10px 2px rgba(124,165,255,0.6)' }}
      />
      <div
        ref={ringRef}
        className="pointer-events-none fixed left-0 top-0 z-[9998] h-8 w-8 -translate-x-1/2 -translate-y-1/2 rounded-full border border-signal-400/40 opacity-0 transition-[opacity,transform,border-color] duration-200"
      />
    </>
  );
}
