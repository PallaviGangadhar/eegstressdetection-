import { useEffect, useRef } from 'react';
import { useReducedMotion } from '@/hooks/useMotion';

type Props = {
  channels?: number;
  className?: string;
  color?: string;
  speed?: number;
};

/** Stacked multi-channel EEG visualization. */
export default function EEGWave({
  channels = 8,
  className = '',
  color = '#38bdf8',
  speed = 1.5,
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

    // Per-channel randomised frequency components
    const channelParams = Array.from({ length: channels }, (_, i) => ({
      freqs: [0.8 + Math.random() * 1.5, 2 + Math.random() * 2, 5 + Math.random() * 3],
      amps: [0.5 + Math.random() * 0.3, 0.2 + Math.random() * 0.2, 0.1 + Math.random() * 0.1],
      phase: Math.random() * Math.PI * 2,
      hueShift: (i % 3) - 1,
    }));

    let offset = 0;
    let raf = 0;
    const draw = () => {
      const cw = w / 2;
      const ch = h / 2;
      ctx.clearRect(0, 0, cw, ch);

      const rowH = ch / channels;
      const steps = Math.ceil(cw);

      for (let c = 0; c < channels; c++) {
        const mid = rowH * (c + 0.5);
        const p = channelParams[c];
        ctx.lineWidth = 1;
        const cstr =
          c === 0
            ? color
            : c % 3 === 1
              ? '#7ca5ff'
              : c % 3 === 2
                ? '#a78bfa'
                : color;
        ctx.strokeStyle = cstr;
        ctx.globalAlpha = 0.8;
        ctx.beginPath();
        for (let i = 0; i <= steps; i++) {
          const t = (i + offset) / 50;
          let val = 0;
          for (let f = 0; f < p.freqs.length; f++) {
            val += Math.sin(t * p.freqs[f] + p.phase + f) * p.amps[f];
          }
          // spike occasionally
          if (Math.sin(t * 0.3 + c) > 0.97) val += 0.4;
          const y = mid - val * rowH * 0.32;
          if (i === 0) ctx.moveTo(i, y);
          else ctx.lineTo(i, y);
        }
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
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
  }, [channels, color, speed, reduced]);

  return <canvas ref={canvasRef} className={className} />;
}
