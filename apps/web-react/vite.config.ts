import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Dev-time proxy to FastAPI so the frontend never needs backend CORS changes; in production
    // the built app is served by FastAPI itself, so requests are same-origin there too.
    proxy: {
      '/stocks': 'http://127.0.0.1:8000',
      '/portfolios': 'http://127.0.0.1:8000',
      '/portfolio-research': 'http://127.0.0.1:8000',
      '/workflows': 'http://127.0.0.1:8000',
      '/strategies': 'http://127.0.0.1:8000',
      '/backtests': 'http://127.0.0.1:8000',
      '/risk': 'http://127.0.0.1:8000',
      '/optimizer': 'http://127.0.0.1:8000',
      '/research-runs': 'http://127.0.0.1:8000',
      '/reports': 'http://127.0.0.1:8000',
      '/data-sources': 'http://127.0.0.1:8000',
      '/macro': 'http://127.0.0.1:8000',
      '/integrations': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
})
