/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        aura: {
          bg: '#07060a',
          surface: '#0f0c1b',
          card: 'rgba(255, 255, 255, 0.03)',
          border: 'rgba(124, 58, 237, 0.20)',
          violet: '#7c3aed',
          neon: '#a855f7',
          cyan: '#06b6d4',
          muted: '#94a3b8'
        }
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(124, 58, 237, 0.15)',
        'glass-hover': '0 12px 40px 0 rgba(168, 85, 247, 0.25)',
        'neon-glow': '0 0 20px rgba(168, 85, 247, 0.4)',
      },
      backdropBlur: {
        'xs': '2px',
        'xl': '20px',
      }
    },
  },
  plugins: [],
}
