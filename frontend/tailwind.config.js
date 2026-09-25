/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#0b1120',
        sidebar: '#080d1a',
        surface: '#131c2e',
        'surface-muted': '#0f1727',
        'surface-hover': '#1a2438',
        line: '#223047',
        'line-strong': '#2e3e59',
        accent: {
          DEFAULT: '#38bdf8',
          hover: '#7dd3fc',
          strong: '#0ea5e9',
          muted: 'rgba(56, 189, 248, 0.12)',
        },
        brand: {
          from: '#38bdf8',
          to: '#818cf8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 0 rgba(255, 255, 255, 0.03) inset, 0 1px 2px rgba(0, 0, 0, 0.3), 0 8px 24px rgba(2, 6, 23, 0.25)',
        pop: '0 16px 40px rgba(2, 6, 23, 0.6), 0 0 0 1px rgba(148, 163, 184, 0.08)',
        glow: '0 0 0 1px rgba(56, 189, 248, 0.35), 0 8px 24px rgba(56, 189, 248, 0.15)',
      },
      borderRadius: {
        card: '0.875rem',
      },
      keyframes: {
        'fade-in': { from: { opacity: '0', transform: 'translateY(4px)' }, to: { opacity: '1', transform: 'none' } },
      },
      animation: {
        'fade-in': 'fade-in 180ms ease-out',
      },
    },
  },
  plugins: [],
}
