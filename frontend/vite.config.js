import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
    // Configuración para desarrollo
    strictPort: false,
    host: true
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    minify: true
  }
})