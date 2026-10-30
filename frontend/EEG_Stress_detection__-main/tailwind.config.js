/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Space Grotesk', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        body: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        ink: {
          950: '#04050a',
          900: '#070912',
          800: '#0b0e1a',
          700: '#12162a',
          600: '#1a1f38',
          500: '#262d4d',
        },
        signal: {
          50: '#eef4ff',
          100: '#d9e6ff',
          200: '#b3cdff',
          300: '#7ca5ff',
          400: '#4878ff',
          500: '#1f5cff',
          600: '#0a3df0',
        },
        bio: {
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
        },
        violet: {
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
        },
      },
      animation: {
        'pulse-soft': 'pulse-soft 4s ease-in-out infinite',
        'float-slow': 'float-slow 12s ease-in-out infinite',
        'drift': 'drift 22s linear infinite',
        'wave-pan': 'wave-pan 6s linear infinite',
      },
      keyframes: {
        'pulse-soft': {
          '0%, 100%': { opacity: '0.55' },
          '50%': { opacity: '1' },
        },
        'float-slow': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-18px)' },
        },
        'drift': {
          '0%': { transform: 'translate(0,0)' },
          '50%': { transform: 'translate(30px,-30px)' },
          '100%': { transform: 'translate(0,0)' },
        },
        'wave-pan': {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-200px)' },
        },
      },
    },
  },
  plugins: [],
};
