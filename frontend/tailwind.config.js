/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#0f172a',
        surface: '#1e293b',
        'surface-muted': '#162033',
        line: '#334155',
        accent: {
          DEFAULT: '#38bdf8',
          hover: '#7dd3fc',
          muted: 'rgba(56, 189, 248, 0.14)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(0, 0, 0, 0.24), 0 8px 24px rgba(2, 6, 23, 0.28)',
        nav: '4px 0 24px rgba(2, 6, 23, 0.35)',
      },
      borderRadius: {
        card: '0.75rem',
      },
    },
  },
  plugins: [],
}
