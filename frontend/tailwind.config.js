/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gold: {
          50: '#FBF7EB',
          100: '#F6ECCB',
          200: '#EDD996',
          300: '#E5C662',
          400: '#DFB73B',
          500: '#D4AF37', // Master Gold
          600: '#B89327',
          700: '#8C6F19',
          800: '#624D11',
          900: '#3C2E0A',
        },
        charcoal: {
          950: '#07090E', // Deepest background
          900: '#0A0D14', // Page canvas
          850: '#0E121B', // Secondary surface
          800: '#121622', // Primary Card
          750: '#181E2E', // Elevated Card
          700: '#222A3F', // Border / Divider
        },
        finpilot: {
          bg: '#07090E',
          card: '#111622',
          text: '#F3F4F6',
          muted: '#9CA3AF',
          border: 'rgba(212, 175, 55, 0.15)',
          primary: '#D4AF37',
          'primary-hover': '#ECC856',
          gold: '#D4AF37',
          champagne: '#F3E5AB',
          lavender: 'rgba(212, 175, 55, 0.12)',
          mint: 'rgba(16, 185, 129, 0.12)',
          blue: 'rgba(56, 189, 248, 0.12)',
          peach: 'rgba(245, 158, 11, 0.12)',
          success: '#10B981',
          warning: '#F59E0B',
          danger: '#F43F5E',
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'card': '0 4px 20px -2px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.06)',
        'card-hover': '0 8px 30px -4px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(212, 175, 55, 0.3)',
        'gold-glow': '0 0 25px rgba(212, 175, 55, 0.2)',
        'modal': '0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(212, 175, 55, 0.25)',
      }
    },
  },
  plugins: [],
}

