import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  worker: {
    format: 'es',
  },
  build: {
    target: 'esnext',
    minify: 'esbuild',
  },
})
