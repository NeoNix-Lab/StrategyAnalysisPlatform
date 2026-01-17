/** @type {import('tailwindcss').Config} */
export default {
    content: [
      "./index.html",
      "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
      extend: {
        colors: {
          // Custom Fintech Dark Palette
          bg: {
            DEFAULT: '#0f172a', // Slate 900
            secondary: '#1e293b', // Slate 800
            tertiary: '#334155', // Slate 700
          },
          accent: {
            DEFAULT: '#38bdf8', // Sky 400
            hover: '#0ea5e9', // Sky 500
            dim: 'rgba(56, 189, 248, 0.1)',
          },
          text: {
            primary: '#f8fafc', // Slate 50
            secondary: '#94a3b8', // Slate 400
            muted: '#64748b', // Slate 500
          },
          success: {
            DEFAULT: '#4ade80', // Green 400
            bg: 'rgba(74, 222, 128, 0.1)',
          },
          danger: {
            DEFAULT: '#f87171', // Red 400
            bg: 'rgba(248, 113, 113, 0.1)',
          },
          warning: '#fbbf24', // Amber 400
        },
        fontFamily: {
          sans: ['Inter', 'system-ui', 'sans-serif'],
          mono: ['JetBrains Mono', 'monospace'],
        },
        backdropBlur: {
          xs: '2px',
        },
        animation: {
          'fade-in': 'fadeIn 0.3s ease-in-out',
          'slide-in': 'slideIn 0.3s ease-out',
        },
        keyframes: {
          fadeIn: {
            '0%': { opacity: '0' },
            '100%': { opacity: '1' },
          },
          slideIn: {
            '0%': { transform: 'translateX(-20px)', opacity: '0' },
            '100%': { transform: 'translateX(0)', opacity: '1' },
          },
        },
      },
    },
    plugins: [],
  }
