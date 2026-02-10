/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'inter': ['Inter', 'sans-serif'],
      },
      colors: {
        // Colores personalizados para el tema del juego
        'werewolf': {
          dark: '#0f172a',
          darker: '#020617',
          slate: '#1e293b',
          'slate-light': '#334155',
        }
      }
    },
  },
  plugins: [],
}