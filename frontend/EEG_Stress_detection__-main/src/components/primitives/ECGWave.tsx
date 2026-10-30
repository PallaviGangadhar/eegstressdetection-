import { useEffect, useRef } from 'react';
import { useReducedMotion } from '@/hooks/useMotion';

type Props = {
  className?: string;
  color?: string;
  speed?: number;
  amplitude?: number;
};

/** Animated ECG waveform drawn on canvas, scrolling left-to-right. */
export default function ECGWave({
  className = '',
  color = '#4878ff',
  speed = 2,
  amplitude = 1,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const reduced = useReducedMotion();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let w = 0;
    let h = 0;
    const setup = () => {
      const rect = canvas.getBoundingClientRect();
      w = canvas.width = rect.width * 2;
      h = canvas.height = rect.height * 2;
      ctx.scale(2, 2);
    };
    setup();

    // Generate a repeating ECG-like pattern
    const ecgPattern = (t: number) => {
      const cycle = t % 1;
      const p = 0.08;
      const q = 0.12;
      const r = 0.14;
      const s = 0.16;
      const tWave = 0.28;
      if (cycle < p) return 0.05 * Math.sin((cycle / p) * Math.PI);
      if (cycle < q) return 0;
      if (cycle < r) return -0.15 * Math.sin(((cycle - q) / (r - q)) * Math.PI);
      if (cycle < s) return 0.9 * Math.sin(((cycle - r) / (s - r)) * Math.PI);
      if (cycle < tWave) return -0.2 * Math.sin(((cycle - s) / (tWave - s)) * Math.PI);
      if (cycle < tWave + 0.1) return 0.15 * Math.sin(((cycle - tWave) / 0.1) * Math.PI);
      return 0;
    };

    let offset = 0;
    let raf = 0;
    const draw = () => {
      const cw = w / 2;
      const ch = h / 2;
      ctx.clearRect(0, 0, cw, ch);

      ctx.lineWidth = 1.5;
      ctx.strokeStyle = color;
      ctx.shadowBlur = 6;
      ctx.shadowColor = color;
      ctx.beginPath();

      const steps = Math.ceil(cw);
      for (let i = 0; i <= steps; i++) {
        const t = (i + offset) / 90;
        const y = ch / 2 - ecgPattern(t) * (ch * 0.4) * amplitude;
        if (i === 0) ctx.moveTo(i, y);
        else ctx.lineTo(i, y);
      }
      ctx.stroke();
      ctx.shadowBlur = 0;

      offset += reduced ? 0 : speed;
      raf = requestAnimationFrame(draw);
    };
    draw();

    const onResize = () => setup();
    window.addEventListener('resize', onResize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', onResize);
    };
  }, [color, speed, amplitude, reduced]);

  return <canvas ref={canvasRef} className={className} />;
}
