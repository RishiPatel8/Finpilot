/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        finpilot: {
          bg: '#F6F8FC',
          card: '#FFFFFF',
          text: '#172033',
          muted: '#697386',
          border: '#E6EAF0',
          primary: '#6478E8',
          'primary-hover': '#5365D6',
          lavender: '#EEF0FF',
          mint: '#E5F7EF',
          blue: '#E8F2FF',
          peach: '#FFF0E5',
          success: '#16865C',
          warning: '#B7791F',
          danger: '#D9485F',
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)',
        'card-hover': '0 4px 12px rgba(23, 32, 51, 0.05)',
        'modal': '0 20px 25px -5px rgba(23, 32, 51, 0.1), 0 8px 10px -6px rgba(23, 32, 51, 0.05)',
      }
    },
  },
  plugins: [],
}

