/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        'rift-red':      '#E2012D',
        'rift-gold':     '#C9A84C',
        'rift-black':    '#0A0A0A',
        'rift-surface':  '#121212',
        'rift-elevated': '#1A1A1A',
        'rift-border':   'rgba(255,255,255,0.08)',
        'rift-success':  '#4CAF50',
        'rift-warning':  '#FFB020',
        'rift-danger':   '#FF5252',
        'rift-text':     '#F5F5F5',
        'rift-muted':    'rgba(255,255,255,0.65)',
      },
      fontFamily: {
        display: ['Bebas Neue', 'sans-serif'],
        ui:      ['Rajdhani', 'sans-serif'],
        body:    ['Inter', 'sans-serif'],
        mono:    ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-red':    'pulseRed 2s ease-in-out infinite',
        'ticker':       'ticker 40s linear infinite',
        'lower-third':  'lowerThird 0.4s cubic-bezier(0.16,1,0.3,1) forwards',
        'score-reveal': 'scoreReveal 0.6s cubic-bezier(0.16,1,0.3,1) forwards',
        'fade-up':      'fadeUp 0.5s ease forwards',
        'shimmer':      'shimmer 1.6s ease-in-out infinite',
      },
      keyframes: {
        pulseRed: {
          '0%,100%': { opacity: '1', boxShadow: '0 0 0 0 rgba(226,1,45,0.4)' },
          '50%':     { opacity: '0.7', boxShadow: '0 0 0 6px rgba(226,1,45,0)' },
        },
        ticker: {
          '0%':   { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
        lowerThird: {
          from: { transform: 'translateY(100%)', opacity: '0' },
          to:   { transform: 'translateY(0)',    opacity: '1' },
        },
        scoreReveal: {
          from: { transform: 'translateY(8px) scaleY(0.9)', opacity: '0' },
          to:   { transform: 'translateY(0) scaleY(1)',     opacity: '1' },
        },
        fadeUp: {
          from: { transform: 'translateY(16px)', opacity: '0' },
          to:   { transform: 'translateY(0)',    opacity: '1' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
}
