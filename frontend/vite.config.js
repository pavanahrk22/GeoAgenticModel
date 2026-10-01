import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/trips': 'http://localhost:8000',
      '/incidents': 'http://localhost:8000',
      '/simulate': 'http://localhost:8000',
    }
  }
});
