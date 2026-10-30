import { useEffect, useRef } from 'react';
import { useReducedMotion } from '@/hooks/useMotion';

type Particle = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  hue: number;
};

/**
 * Living scientific background — slow drifting glowing particles with
 * faint neural-network connection lines, waveform curves, sparks, and
 * a grid. Canvas-based for performance.
 */
export default function AnimatedBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const reduced = useReducedMotion();

  useEffect(() => {
    if (reduced) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let w = (canvas.width = window.innerWidth);
    let h = (canvas.height = window.innerHeight);
    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    const setupCanvas = () => {
      w = window.innerWidth;
      h = window.innerHeight;
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = w + 'px';
      canvas.style.height = h + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    setupCanvas();

    const isMobile = w < 768;
    const count = isMobile ? 32 : 70;
    const particles: Particle[] = Array.from({ length: count }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.18,
      vy: (Math.random() - 0.5) * 0.18,
      r: Math.random() * 1.4 + 0.4,
      hue: Math.random() > 0.5 ? 220 : 250,
    }));

    // sparks that travel across
    const sparks: {
      x: number;
      y: number;
      vx: number;
      life: number;
      maxLife: number;
    }[] = [];

    let frame = 0;
    let raf = 0;

    const draw = () => {
      ctx.clearRect(0, 0, w, h);

      // grid
      ctx.strokeStyle = 'rgba(72,120,255,0.04)';
      ctx.lineWidth = 1;
      const gridSize = 80;
      const offset = (frame * 0.05) % gridSize;
      ctx.beginPath();
      for (let x = -offset; x < w; x += gridSize) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
      }
      for (let y = -offset; y < h; y += gridSize) {
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
      }
      ctx.stroke();

      // radial glow
      const grad = ctx.createRadialGradient(w * 0.5, h * 0.35, 0, w * 0.5, h * 0.35, w * 0.6);
      grad.addColorStop(0, 'rgba(31,92,255,0.05)');
      grad.addColorStop(1, 'rgba(31,92,255,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);

      // particles + connections
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${p.hue}, 90%, 70%, 0.5)`;
        ctx.fill();

        // connections
        for (let j = i + 1; j < particles.length; j++) {
          const q = particles[j];
          const dx = p.x - q.x;
          const dy = p.y - q.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 130) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(q.x, q.y);
            ctx.strokeStyle = `hsla(225, 80%, 65%, ${(1 - dist / 130) * 0.12})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }

      // occasional spark
      if (frame % 180 === 0 && Math.random() > 0.4) {
        const fromLeft = Math.random() > 0.5;
        sparks.push({
          x: fromLeft ? -20 : w + 20,
          y: Math.random() * h,
          vx: fromLeft ? 2 + Math.random() * 2 : -(2 + Math.random() * 2),
          life: 0,
          maxLife: 80,
        });
      }

      // update + draw sparks
      for (let i = sparks.length - 1; i >= 0; i--) {
        const s = sparks[i];
        s.x += s.vx;
        s.life++;
        const alpha = Math.sin((s.life / s.maxLife) * Math.PI) * 0.8;
        ctx.beginPath();
        ctx.arc(s.x, s.y, 1.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(124,165,255,${alpha})`;
        ctx.shadowBlur = 8;
        ctx.shadowColor = 'rgba(124,165,255,0.8)';
        ctx.fill();
        ctx.shadowBlur = 0;
        // trail
        ctx.beginPath();
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(s.x - s.vx * 4, s.y);
        ctx.strokeStyle = `rgba(124,165,255,${alpha * 0.4})`;
        ctx.lineWidth = 1;
        ctx.stroke();
        if (s.life >= s.maxLife) sparks.splice(i, 1);
      }

      frame++;
      raf = requestAnimationFrame(draw);
    };
    draw();

    const onResize = () => setupCanvas();
    window.addEventListener('resize', onResize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', onResize);
    };
  }, [reduced]);

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden bg-ink-950">
      {/* gradient layers */}
      <div className="absolute inset-0 bg-gradient-to-b from-ink-900 via-ink-950 to-ink-900" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(31,92,255,0.08),transparent_60%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,rgba(139,92,246,0.06),transparent_55%)]" />
      {!reduced && <canvas ref={canvasRef} className="absolute inset-0" />}
      {/* waveform curves at bottom */}
      {!reduced && (
        <svg
          className="absolute bottom-0 left-0 w-full opacity-20"
          height="160"
          viewBox="0 0 1200 160"
          preserveAspectRatio="none"
          fill="none"
        >
          <path
            d="M0,80 Q150,20 300,80 T600,80 T900,80 T1200,80"
            stroke="rgba(72,120,255,0.3)"
            strokeWidth="1"
          />
          <path
            d="M0,100 Q150,60 300,100 T600,100 T900,100 T1200,100"
            stroke="rgba(139,92,246,0.2)"
            strokeWidth="1"
          />
        </svg>
      )}
    </div>
  );
}
