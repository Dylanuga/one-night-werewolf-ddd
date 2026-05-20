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
    host: true,
    proxy: {
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true
      },
      '/test': {
        target: 'http://localhost:5000'
      },
      '/debug': {
        target: 'http://localhost:5000'
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    minify: true
  }
})